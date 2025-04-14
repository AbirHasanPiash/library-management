from rest_framework import serializers
from .models import Member, Book, Author, Category, Borrow, Reservation


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'email', 'first_name', 'last_name', 'membership_date', 'address', 'phone_number', 'is_active']
        read_only_fields = ['id', 'email', 'membership_date']

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if not user.is_staff:
            validated_data.pop('is_active', None)
        return super().update(instance, validated_data)


class MemberCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Member
        fields = ['email', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        return Member.objects.create_user(**validated_data)



class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'biography']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Author.objects.all(), write_only=True, source='authors'
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, source='category'
    )

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'isbn',
            'authors', 'author_ids',
            'category', 'category_id',
            'total_copies', 'available_copies'
        ]

    def validate(self, data):
        total = data.get('total_copies', getattr(self.instance, 'total_copies', None))
        available = data.get('available_copies', getattr(self.instance, 'available_copies', None))

        if total is not None and available is not None and total < available:
            raise serializers.ValidationError({
                'available_copies': 'Available copies cannot exceed total copies.'
            })

        return data

class BorrowSerializer(serializers.ModelSerializer):
    member_email = serializers.EmailField(source='member.email', read_only=True)
    book_detail = BookSerializer(source='book', read_only=True)

    class Meta:
        model = Borrow
        fields = [
            'id',
            'member',
            'member_email',
            'book',
            'book_detail',
            'borrow_date',
            'due_date',
            'return_date',
            'fine',
        ]
        read_only_fields = ['member', 'fine']


class ReservationSerializer(serializers.ModelSerializer):
    member_email = serializers.EmailField(source='member.email', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'member', 'member_email', 'book', 'book_title', 'reservation_date', 'is_active']
        read_only_fields = ['member']