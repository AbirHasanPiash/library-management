from django_filters.rest_framework import DjangoFilterBackend
from .serializers import MemberSerializer, AuthorSerializer, CategorySerializer, BookSerializer,\
    BorrowSerializer, ReservationSerializer
from .models import Member, Category, Book, Author, Borrow, Reservation
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import viewsets, permissions, filters
from .permissions import IsAdminOrSelf
from datetime import date
from rest_framework.decorators import action
from .permissions import IsAdminOrSelf, IsAdminOrReadOnly

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            return [permissions.IsAdminUser()]
        elif self.action == 'me':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdminOrSelf()]

    @action(detail=False, methods=['get', 'put'], url_path='me')
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['category__name', 'authors__first_name', 'authors__last_name']
    search_fields = ['title', 'authors__name', 'category__name']
    ordering_fields = ['title', 'available_copies']

    def get_queryset(self):
        return Book.objects.select_related('category').prefetch_related('authors')


class BorrowViewSet(viewsets.ModelViewSet):
    serializer_class = BorrowSerializer
    permission_classes = [IsAdminOrSelf]

    def get_queryset(self):
        qs = Borrow.objects.select_related('member', 'book', 'book__category')\
                        .prefetch_related('book__authors')

        if self.request.user.is_staff:
            return qs

        if self.request.user.is_authenticated:
            return qs.filter(member=self.request.user)

        return Borrow.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(member=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def return_book(self, request, pk=None):
        borrow = self.get_object()
        if borrow.return_date:
            return Response({"detail": "Book already returned."}, status=status.HTTP_400_BAD_REQUEST)

        borrow.return_date = timezone.now().date()
        borrow.book.available_copies += 1
        borrow.book.save()
        borrow.save()
        return Response({"detail": "Book returned successfully."})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def overdue(self, request):
        today = date.today()
        overdue_borrows = Borrow.objects.filter(return_date__isnull=True, due_date__lt=today).select_related('book', 'member')
        serializer = self.get_serializer(overdue_borrows, many=True)
        return Response(serializer.data)


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSelf]

    def get_queryset(self):
        qs = Reservation.objects.select_related('member', 'book', 'book__category')
        if self.request.user.is_staff:
            return qs
        return qs.filter(member=self.request.user)

    def perform_create(self, serializer):
        serializer.save(member=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        if not reservation.is_active:
            return Response({"detail": "Reservation already canceled."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.is_active = False
        reservation.save()
        return Response({"detail": "Reservation canceled successfully."})