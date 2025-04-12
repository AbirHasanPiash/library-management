from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from .managers import MemberManager


class Member(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    membership_date = models.DateField(default=timezone.now)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = MemberManager()

    def __str__(self):
        return self.email


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    biography = models.TextField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author)
    isbn = models.CharField(max_length=13)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    total_copies = models.IntegerField(validators=[MinValueValidator(0)])
    available_copies = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return self.title


class Borrow(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.member.email} borrowed {self.book.title}"


class Reservation(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reservation_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.member.email} reserved {self.book.title}"
