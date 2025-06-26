from rest_framework import serializers
from .models import File, FileAccessLog
from django.utils import timezone

class FileAccessLogSerializer(serializers.ModelSerializer):
    log_at = serializers.SerializerMethodField()

    class Meta:
        model = FileAccessLog
        fields = ['log_at', 'ip_address', 'user_agent']

    def get_log_at(self, obj):
        local_time = timezone.localtime(obj.log_at)
        return local_time.strftime('%d.%m.%Y %H:%M')

class FileSerializer(serializers.ModelSerializer):
    expires_at = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    access_logs = FileAccessLogSerializer(many=True, read_only=True)

    class Meta:
        model = File
        fields = ['id', 'file', 'link', 'expire_hours', 'expires_at', 'creator', 'created_at', 'updated_at', 'access_logs']
        read_only_fields = ['link', 'created_at', 'updated_at', 'expires_at', 'creator', 'access_logs']

    def get_expires_at(self, obj):
        local_time = timezone.localtime(obj.expires_at)
        return local_time.strftime('%d.%m.%Y %H:%M')

    def get_created_at(self, obj):
        local_time = timezone.localtime(obj.created_at)
        return local_time.strftime('%d.%m.%Y %H:%M')

    def get_updated_at(self, obj):
        local_time = timezone.localtime(obj.updated_at)
        return local_time.strftime('%d.%m.%Y %H:%M')