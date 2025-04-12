from rest_framework import serializers
from .models import Member, Book, Author, Category, Borrow, Reservation
from django.contrib.auth.hashers import make_password
from datetime import timedelta, date

class MemberRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['email', 'first_name', 'last_name', 'password', 'address', 'phone_number']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'email', 'first_name', 'last_name', 'address', 'phone_number', 'membership_date']



class BookCreateSerializer(serializers.ModelSerializer):
    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), many=True, write_only=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True
    )

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn', 'total_copies', 'available_copies',
            'author_ids', 'category_id'
        ]

    def validate(self, data):
        total = data.get('total_copies')
        available = data.get('available_copies')

        if total is not None and available is not None:
            if available > total:
                raise serializers.ValidationError(
                    "Available copies cannot be greater than total copies."
                )
        return data

    def create(self, validated_data):
        authors = validated_data.pop('author_ids')
        category = validated_data.pop('category_id')
        book = Book.objects.create(category=category, **validated_data)
        book.authors.set(authors)
        return book



class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'biography']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'authors', 'isbn', 'category',
            'total_copies', 'available_copies'
        ]


class BookUpdateSerializer(serializers.ModelSerializer):
    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), many=True, write_only=True, required=False
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = Book
        fields = [
            'title', 'isbn', 'total_copies', 'available_copies',
            'author_ids', 'category_id'
        ]

    def update(self, instance, validated_data):
        authors = validated_data.pop('author_ids', None)
        category = validated_data.pop('category_id', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if category:
            instance.category = category
        if authors:
            instance.authors.set(authors)

        instance.save()
        return instance
    

class BorrowSerializer(serializers.ModelSerializer):
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source='book', write_only=True
    )

    class Meta:
        model = Borrow
        fields = ['id', 'book_id', 'borrow_date', 'due_date']
        read_only_fields = ['borrow_date', 'due_date']

    def validate(self, attrs):
        book = attrs['book']
        if book.available_copies < 1:
            raise serializers.ValidationError("This book is currently not available.")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        book = validated_data['book']

        book.available_copies -= 1
        book.save()

        borrow_date = date.today()
        due_date = borrow_date + timedelta(days=14)

        borrow = Borrow.objects.create(
            member=user,
            book=book,
            borrow_date=borrow_date,
            due_date=due_date
        )
        return borrow
    

class ReturnBookSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()

    def validate(self, data):
        user = self.context['request'].user
        book_id = data['book_id']
        try:
            borrow = Borrow.objects.get(
                member=user,
                book_id=book_id,
                return_date__isnull=True
            )
            data['borrow'] = borrow
        except Borrow.DoesNotExist:
            raise serializers.ValidationError("No active borrow record found for this book.")
        return data
    
    def save(self, **kwargs):
        user = self.context['request'].user
        borrow = self.validated_data['borrow']
        borrow.return_date = date.today()
        borrow.save()

        book = borrow.book
        book.available_copies += 1
        book.save()

        response_data = {
            "message": "Book returned successfully.",
            "book_returned": {
                "title": book.title,
                "borrow_date": borrow.borrow_date,
                "due_date": borrow.due_date,
                "return_date": borrow.return_date
            }
        }

        if borrow.return_date > borrow.due_date:
            late_days = (borrow.return_date - borrow.due_date).days
            response_data.update({
                "late": True,
                "late_days": late_days,
                "fine": late_days * 10
            })
        else:
            response_data["late"] = False

        active_borrows = Borrow.objects.filter(member=user, return_date__isnull=True)
        response_data["currently_borrowed_books"] = [
            {
                "id": b.book.id,
                "title": b.book.title,
                "borrow_date": b.borrow_date,
                "due_date": b.due_date
            } for b in active_borrows
        ]

        return response_data

    

class BorrowRecordSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    member = MemberSerializer(read_only=True)

    class Meta:
        model = Borrow
        fields = ['id', 'member', 'book', 'borrow_date', 'due_date', 'return_date']


class ReservationSerializer(serializers.ModelSerializer):
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source='book', write_only=True
    )

    class Meta:
        model = Reservation
        fields = ['id', 'book_id', 'reservation_date', 'is_active']
        read_only_fields = ['reservation_date', 'is_active']

    def validate(self, data):
        user = self.context['request'].user
        book = data['book']

        if book.available_copies > 0:
            raise serializers.ValidationError("This book is available. No need to reserve.")

        if Reservation.objects.filter(book=book, member=user, is_active=True).exists():
            raise serializers.ValidationError("You have already reserved this book.")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        book = validated_data['book']
        return Reservation.objects.create(
            member=user,
            book=book,
            reservation_date=date.today(),
            is_active=True
        )
    

class CancelReservationSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()

    def validate(self, data):
        user = self.context['request'].user
        book_id = data['book_id']

        try:
            reservation = Reservation.objects.get(
                book_id=book_id,
                member=user,
                is_active=True
            )
            data['reservation'] = reservation
        except Reservation.DoesNotExist:
            raise serializers.ValidationError("No active reservation found for this book.")

        return data

    def save(self, **kwargs):
        reservation = self.validated_data['reservation']
        reservation.is_active = False
        reservation.save()
        return {"message": "Reservation cancelled successfully."}
    

class ReservationRecordSerializer(serializers.ModelSerializer):
    member = MemberSerializer(read_only=True)
    book = BookSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'member', 'book', 'reservation_date', 'is_active']