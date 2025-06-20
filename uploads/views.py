from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import File, FileAccessLog
from .serializers import FileSerializer, FileAccessLogSerializer
import secrets
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import FileResponse, HttpResponse
import requests

@swagger_auto_schema(
    method='post',
    operation_description="Fayl yuklash (expire_hours soat ichida o'chiriladi)",
    tags=['file'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['file', 'expire_hours'],
        properties={
            'file': openapi.Schema(type=openapi.TYPE_STRING, format='binary', description='Fayl'),
            'expire_hours': openapi.Schema(type=openapi.TYPE_INTEGER, description='Necha soatdan keyin o\'chiriladi')
        }
    ),
    responses={
        201: FileSerializer,
        400: 'Noto\'g\'ri so\'rov'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_file(request):
    uploaded_file = request.FILES.get('file')
    expire_hours = int(request.data.get('expire_hours', 24))
    if not uploaded_file:
        return Response({'error': 'Fayl talab qilinadi'}, status=status.HTTP_400_BAD_REQUEST)
    file_obj = File.objects.create(
        file=uploaded_file,
        creator=request.user,
        expire_hours=expire_hours,
        link=secrets.token_urlsafe(16)
    )
    serializer = FileSerializer(file_obj)
    download_url = request.build_absolute_uri(f'/file/{file_obj.link}/')
    data = serializer.data
    data['download_url'] = download_url
    return Response(data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='get',
    operation_description="Mening yuklangan fayllarim va ularning loglari",
    tags=['file'],
    responses={
        200: FileSerializer(many=True)
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_files(request):
    files = File.objects.filter(creator=request.user)
    data = []
    for file in files:
        file_data = FileSerializer(file).data
        logs = FileAccessLog.objects.filter(file=file)
        file_data['access_logs'] = FileAccessLogSerializer(logs, many=True).data
        data.append(file_data)
    return Response(data)

@swagger_auto_schema(
    method='get',
    operation_description="Faylni havola orqali olish (havola muddati tugamagan bo'lishi kerak)",
    tags=['file'],
    manual_parameters=[
        openapi.Parameter('link', openapi.IN_PATH, description="Fayl uchun unikal havola", type=openapi.TYPE_STRING)
    ],
    responses={
        200: 'Fayl muvaffaqiyatli yuklandi',
        404: 'Fayl topilmadi',
        410: 'Havola muddati tugagan'
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_file_by_link(request, link):
    file_obj = File.objects.filter(link=link).first()
    if not file_obj:
        return HttpResponse("Fayl topilmadi", status=404)
    
    expires_at = file_obj.created_at + timezone.timedelta(hours=file_obj.expire_hours)
    if timezone.now() > expires_at:
        return HttpResponse("Havola muddati tugagan", status=410)

    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    FileAccessLog.objects.create(
        file=file_obj,
        ip_address=ip,
        user_agent=user_agent
    )

    response = FileResponse(file_obj.file.open('rb'), as_attachment=True, filename=file_obj.file.name.split('/')[-1])
    return response
