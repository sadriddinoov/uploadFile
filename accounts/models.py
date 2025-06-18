from django.contrib.auth.models import AbstractUser
from django.db import models
from random import randint
from uuid import uuid4


class User(AbstractUser):
    is_verify = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=13, unique=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username or self.phone_number or f"User #{self.id}"

class OTP(models.Model):
    user = models.ForeignKey("User",on_delete=models.CASCADE,related_name="otp_user")
    key = models.UUIDField(default=uuid4)
    code = models.PositiveIntegerField(default=randint(1000,10000))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username