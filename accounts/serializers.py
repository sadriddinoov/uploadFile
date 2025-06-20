from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import OTP

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ('username', 'phone_number', 'password')
        extra_kwargs = {'password': {'write_only': True}}

class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['id', 'key', 'code', 'created_at', 'updated_at']
        read_only_fields = ['key', 'code', 'created_at', 'updated_at']