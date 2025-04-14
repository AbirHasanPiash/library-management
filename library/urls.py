from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MemberViewSet, AuthorViewSet, CategoryViewSet, BookViewSet,\
    BorrowViewSet, ReservationViewSet

router = DefaultRouter()
router.register(r'members', MemberViewSet, basename='member')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'books', BookViewSet, basename='book')
router.register(r'borrows', BorrowViewSet, basename='borrow')
router.register(r'reservations', ReservationViewSet, basename='reservations')

urlpatterns = [
    path('', include(router.urls)),             # Your custom member routes
    path('auth/', include('djoser.urls')),          # Djoser endpoints
    path('auth/', include('djoser.urls.jwt')),      # Djoser JWT endpoints
]