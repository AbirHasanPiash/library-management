from rest_framework import generics
from .serializers import MemberRegistrationSerializer, MemberSerializer, BookSerializer,\
    BookCreateSerializer, BookUpdateSerializer, AuthorSerializer, BorrowSerializer, \
    ReturnBookSerializer, BorrowRecordSerializer, ReservationSerializer, \
    CancelReservationSerializer, ReservationRecordSerializer, CategorySerializer
from .models import Member, Category, Book, Author, Borrow, Reservation
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django.db.models import Q
from rest_framework import status
from django.utils import timezone


class MemberRegisterView(generics.CreateAPIView):
    queryset = Member.objects.all()
    serializer_class = MemberRegistrationSerializer


class BookSearchView(generics.ListAPIView):
    serializer_class = BookSerializer
    filter_backends = [SearchFilter,]
    search_fields = ['title', 'authors__first_name', 'authors__last_name', 'category__name']

    def get_queryset(self):
        query = self.request.query_params.get('query', '')
        return Book.objects.filter(
            Q(title__icontains=query) |
            Q(authors__first_name__icontains=query) |
            Q(authors__last_name__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryCreateView(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]


class CategoryUpdateView(generics.UpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]


class CategoryDeleteView(generics.DestroyAPIView):
    queryset = Category.objects.all()
    permission_classes = [IsAdminUser]


class MemberListView(generics.ListAPIView):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAdminUser]


class MemberDetailView(generics.RetrieveAPIView):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAdminUser]


class BookCreateView(generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookCreateSerializer
    permission_classes = [IsAdminUser]


class BookListView(generics.ListAPIView):
    queryset = Book.objects.select_related('category').prefetch_related('authors')
    serializer_class = BookSerializer


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookUpdateView(generics.UpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookUpdateSerializer
    permission_classes = [IsAdminUser]


class BookDeleteView(generics.DestroyAPIView):
    queryset = Book.objects.all()
    permission_classes = [IsAdminUser]


class AuthorListView(generics.ListAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class AuthorCreateView(generics.CreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminUser]


class AuthorDetailView(generics.RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class AuthorUpdateView(generics.UpdateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminUser]


class AuthorDeleteView(generics.DestroyAPIView):
    queryset = Author.objects.all()
    permission_classes = [IsAdminUser]


class BorrowBookView(generics.CreateAPIView):
    serializer_class = BorrowSerializer
    permission_classes = [IsAuthenticated]


class ReturnBookView(generics.GenericAPIView):
    serializer_class = ReturnBookSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    

class BorrowListView(generics.ListAPIView):
    queryset = Borrow.objects.select_related(
        'book__category',
        'member'
    ).prefetch_related('book__authors')
    serializer_class = BorrowRecordSerializer
    permission_classes = [IsAdminUser]


class MemberBorrowHistoryView(generics.ListAPIView):
    serializer_class = BorrowRecordSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        member_id = self.kwargs['pk']
        return Borrow.objects.filter(member_id=member_id)
    

class ReserveBookView(generics.CreateAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]


class CancelReservationView(generics.GenericAPIView):
    serializer_class = CancelReservationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = serializer.save()
        return Response(response_data, status=status.HTTP_200_OK)
    

class ReservationListView(generics.ListAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationRecordSerializer
    permission_classes = [IsAdminUser]


class OverdueBooksView(generics.ListAPIView):
    serializer_class = BorrowRecordSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        today = timezone.now().date()
        return Borrow.objects.filter(return_date__isnull=True, due_date__lt=today)