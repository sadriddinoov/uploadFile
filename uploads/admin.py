from django.contrib import admin
from .models import File, FileAccessLog

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "creator", "expire_hours", "created_at", "updated_at")
    search_fields = ("file", "creator__username")
    list_filter = ("creator", "expire_hours", "created_at")
    ordering = ("-created_at",)

@admin.register(FileAccessLog)
class FileAccessLogAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "log_at", "ip_address", "user_agent")
    search_fields = ("file__file", "ip_address")
    list_filter = ("file", "log_at")
    ordering = ("-log_at",)
