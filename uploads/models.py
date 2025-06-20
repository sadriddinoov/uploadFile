from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

# Create your models here.

class File(models.Model):
    file = models.FileField(upload_to='files/')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='files')
    expire_hours = models.PositiveIntegerField(default=24, help_text="Necha soatdan keyin o'chiriladi")
    link = models.CharField(max_length=32, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def expires_at(self):
        return self.created_at + timedelta(hours=self.expire_hours)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.file.name} ({self.creator})"

class FileAccessLog(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='access_logs')
    log_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.file.file.name} - {self.ip_address} - {self.log_at}"
