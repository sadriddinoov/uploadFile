from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import OTP

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'phone_number')
        read_only_fields = ('password',)

class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['id', 'key', 'code', 'created_at', 'updated_at']
        read_only_fields = ['key', 'code', 'created_at', 'updated_at']