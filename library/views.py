from django_filters.rest_framework import DjangoFilterBackend
from .serializers import MemberSerializer, AuthorSerializer, CategorySerializer, BookSerializer,\
    BorrowSerializer, ReservationSerializer
from .models import Member, Category, Book, Author, Borrow, Reservation
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import serializers, viewsets, permissions, filters
from .permissions import IsAdminOrSelf
from datetime import date
from rest_framework.decorators import action
from .permissions import IsAdminOrSelf, IsAdminOrReadOnly

class MemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Member instances.

    This viewset provides full CRUD operations for the custom Member model.
    - Only admin users can list, create, or delete members.
    - Authenticated users can view and update their own profile via the 'me' endpoint.
    - Permissions are dynamically assigned based on the action being performed.

    Custom Actions:
    - me (GET): Returns the current authenticated user's profile data.
    - me (PUT): Allows the authenticated user to partially update their own profile.
    """
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
    """
    ViewSet for managing Author instances.

    Provides full CRUD operations on authors.
    - Read operations are accessible to all users.
    - Write operations (create, update, delete) are restricted to admin users only.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Category instances.

    Provides full CRUD operations on book categories.
    - Read operations are accessible to all users.
    - Write operations (create, update, delete) are restricted to admin users only.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]



class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Book instances.

    Provides full CRUD operations on books.
    - Read operations are available to all users.
    - Write operations (create, update, delete) are restricted to admin users.

    Features:
    - Filtering by category name and author name fields.
    - Searching by book title, author name, and category name.
    - Ordering by title and number of available copies.
    """
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['category__name', 'authors__first_name', 'authors__last_name']
    search_fields = ['title', 'authors__name', 'category__name']
    ordering_fields = ['title', 'available_copies']

    def get_queryset(self):
        return Book.objects.select_related('category').prefetch_related('authors')



class BorrowViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing borrowing of books by members.

    - Admins can view, create, and manage all borrow records.
    - Members can view and create their own borrow records.
    - Books cannot be borrowed if no available copies exist.
    - Automatically decreases the available copies on borrow.
    - Includes custom actions for returning books and viewing overdue borrows.
    """
    serializer_class = BorrowSerializer
    permission_classes = [IsAdminOrSelf]

    def get_queryset(self):
        """
        Returns a queryset of borrow records:
        - All records for admin users.
        - Only the user's own records for authenticated members.
        - None for unauthenticated or anonymous users (e.g., during schema generation).
        """
        qs = Borrow.objects.select_related('member', 'book', 'book__category')\
                        .prefetch_related('book__authors')

        user = getattr(self.request, 'user', None)
        if user and user.is_staff:
            return qs

        if user and user.is_authenticated:
            return qs.filter(member=user)

        return Borrow.objects.none()

    def perform_create(self, serializer):
        """
        Handles borrowing a book.

        - Validates book availability.
        - Decreases book's available copies.
        - Assigns the authenticated user as member if not admin.
        """
        book = serializer.validated_data['book']

        if book.available_copies < 1:
            raise serializers.ValidationError({"detail": "No copies available for borrowing."})

        book.available_copies -= 1
        book.save()

        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(member=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def return_book(self, request, pk=None):
        """
        Marks a borrowed book as returned.

        - Sets the return date.
        - Increments the book's available copies.
        - Fails if the book is already returned.
        """
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
        """
        Lists all overdue borrow records (unreturned books past due date).

        - Admin only access.
        - Includes member and book details.
        """
        today = date.today()
        overdue_borrows = Borrow.objects.filter(return_date__isnull=True, due_date__lt=today).select_related('book', 'member')
        serializer = self.get_serializer(overdue_borrows, many=True)
        return Response(serializer.data)



class ReservationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing book reservations.

    - Authenticated users can create and view their own reservations.
    - Admins can access all reservations.
    - Includes functionality to cancel active reservations.
    """
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSelf]

    def get_queryset(self):
        """
        Returns the queryset of reservations:
        - All reservations for admin users.
        - Only the authenticated user's reservations otherwise.
        - Returns empty queryset for anonymous or unauthenticated users (e.g., during schema generation).
        """
        qs = Reservation.objects.select_related('member', 'book', 'book__category')
        user = getattr(self.request, 'user', None)
        if user and user.is_staff:
            return qs
        if user and user.is_authenticated:
            return qs.filter(member=user)
        return Reservation.objects.none()

    def perform_create(self, serializer):
        """
        Creates a new reservation.

        - Automatically assigns the reservation to the authenticated user.
        """
        serializer.save(member=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Cancels an active reservation.

        - Sets `is_active` to False.
        - Fails if the reservation is already canceled.
        """
        reservation = self.get_object()
        if not reservation.is_active:
            return Response({"detail": "Reservation already canceled."}, status=status.HTTP_400_BAD_REQUEST)
        reservation.is_active = False
        reservation.save()
        return Response({"detail": "Reservation canceled successfully."})
