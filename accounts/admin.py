from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "phone_number", "is_verify")
    search_fields = ("username", "phone_number")