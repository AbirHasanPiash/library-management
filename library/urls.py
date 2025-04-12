from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.MemberRegisterView.as_view(), name='register'),

    path('search/', views.BookSearchView.as_view(), name='book-search'),

    path('members/', views.MemberListView.as_view(), name='member-list'),
    path('members/<int:pk>/', views.MemberDetailView.as_view(), name='member-detail'),

    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),

    path('books/add/', views.BookCreateView.as_view(), name='book-create'),
    path('books/', views.BookListView.as_view(), name='book-list'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('books/<int:pk>/update/', views.BookUpdateView.as_view(), name='book-update'),
    path('books/<int:pk>/delete/', views.BookDeleteView.as_view(), name='book-delete'),

    path('authors/', views.AuthorListView.as_view(), name='author-list'),
    path('authors/add/', views.AuthorCreateView.as_view(), name='author-create'),
    path('authors/<int:pk>/', views.AuthorDetailView.as_view(), name='author-detail'),
    path('authors/<int:pk>/update/', views.AuthorUpdateView.as_view(), name='author-update'),
    path('authors/<int:pk>/delete/', views.AuthorDeleteView.as_view(), name='author-delete'),

    path('borrow/', views.BorrowBookView.as_view(), name='borrow-book'),
    path('return/', views.ReturnBookView.as_view(), name='return-book'),
    path('borrows/', views.BorrowListView.as_view(), name='borrow-list'),
    path('members/<int:pk>/borrows/', views.MemberBorrowHistoryView.as_view(), name='member-borrow-history'),

    path('reserve/', views.ReserveBookView.as_view(), name='reserve-book'),
    path('cancel-reservation/', views.CancelReservationView.as_view(), name='cancel-reservation'),
    path('overdue/', views.OverdueBooksView.as_view(), name='overdue-books'),
]
