from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Member, Author, Book, Category, Borrow, Reservation
from django.utils.translation import gettext_lazy as _


@admin.register(Member)
class MemberAdmin(UserAdmin):
    model = Member
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'address', 'phone_number', 'membership_date')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active')}
        ),
    )

    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

admin.site.register(Author)
admin.site.register(Book)
admin.site.register(Category)
admin.site.register(Borrow)
admin.site.register(Reservation)