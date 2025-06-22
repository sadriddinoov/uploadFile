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
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@swagger_auto_schema(
    method='post',
    operation_description="Fayl yuklash (expire_hours soat ichida o'chiriladi)",
    tags=['file'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['file', 'expire_hours'],
        properties={
            'file': openapi.Schema(type=openapi.TYPE_STRING, description='Fayl'),
            'expire_hours': openapi.Schema(type=openapi.TYPE_INTEGER, description="Necha soatdan keyin o'chiriladi")
        }
    ),
    responses={
        201: FileSerializer,
        400: "Noto'g'ri so'rov"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_file(request):
    uploaded_file = request.FILES.get('file')
    expire_hours = int(request.data.get('expire_hours', 24))
    if not uploaded_file:
        return Response({'error': 'Fayl yuklash shart'}, status=status.HTTP_400_BAD_REQUEST)
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
    operation_description="Yuklangan fayilarim va fayilani loglari",
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
    operation_description="Faylni link orqali olish",
    tags=['file'],
    manual_parameters=[
        openapi.Parameter('link', openapi.IN_PATH, description="Fayl uchun unikal link", type=openapi.TYPE_STRING)
    ],
    responses={
        200: 'Fayl muvaffaqiyatli yuklandi',
        404: 'Fayl topilmadi'
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_file_by_link(request, link):
    file_obj = File.objects.filter(link=link).first()
    if not file_obj:
        return HttpResponse("Fayl topilmadi", status=status.HTTP_404_NOT_FOUND)
    
    expires_at = file_obj.created_at + timezone.timedelta(hours=file_obj.expire_hours)
    if timezone.now() > expires_at:
        return HttpResponse("Link muddati tugagan", status=status.HTTP_410_GONE)

    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    FileAccessLog.objects.create(
        file=file_obj,
        ip_address=ip,
        user_agent=user_agent
    )

    response = FileResponse(file_obj.file.open('rb'), as_attachment=True, filename=file_obj.file.name.split('/')[-1])
    return response


# WEB

@login_required(login_url="/auth/web-login/")
def upload_file_page(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        expire_hours = int(request.POST.get('expire_hours', 24))
        if uploaded_file:
            File.objects.create(
                file=uploaded_file,
                creator=request.user,
                expire_hours=expire_hours,
                link=secrets.token_urlsafe(16)
            )
            messages.success(request, 'Fayl yuklandi')
            return redirect('my_files_page')
    return render(request, 'uploads/upload.html')

@login_required(login_url="/auth/web-login/")
def my_files_page(request):
    files = File.objects.filter(creator=request.user).order_by('-id')
    return render(request, 'uploads/my_files.html', {'files': files})

@permission_classes([AllowAny])
def download_file_page(request, link):
    file_obj = File.objects.filter(link=link).first()
    if not file_obj:
        return render(request, 'uploads/download.html', {'error': 'Fayil topilmadi'})
    expires_at = file_obj.created_at + timezone.timedelta(hours=file_obj.expire_hours)
    if timezone.now() > expires_at:
        return render(request, 'uploads/download.html', {'error': 'Link muddati tugagan'})

    cookie_name = f'used_{file_obj.link}'
    already_used = request.COOKIES.get(cookie_name, None)

    if already_used:
        return render(request, 'uploads/download.html', {'error': 'Bu faylga ushbu qurilmadan faqat bir marta kirish mumkin (link ishlatilgan).'})

    if request.method == 'POST':
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        FileAccessLog.objects.create(
            file=file_obj,
            ip_address=ip,
            user_agent=user_agent
        )
        
        response = FileResponse(file_obj.file.open('rb'), filename=file_obj.file.name.split('/')[-1])
        response.set_cookie(cookie_name, '1', max_age=60*60*24*7)
        return response

    return render(request, 'uploads/download.html', {'file': file_obj})