from django.contrib.auth import authenticate, login as django_login, logout
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import OTP
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, OTPSerializer
from random import randint
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg import openapi
from django.shortcuts import render, redirect
import requests


User = get_user_model()

@swagger_auto_schema(
    methods=['POST'],
    request_body=UserSerializer,
    responses={
        201: openapi.Response(
            description="Foydalanuvchi muvaffaqiyatli yaratildi",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'otp_key': openapi.Schema(type=openapi.TYPE_STRING, description='Tasdiqlash uchun OTP kaliti'),
                    'otp_code': openapi.Schema(type=openapi.TYPE_STRING, description='OTP kodi')
                }
            )
        ),
        400: "Noto'g'ri so'rov"
    },
    operation_description="Yangi foydalanuvchi qo'shish",
    tags=['auth']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    data = request.data
    serializer = UserSerializer(data=data)
    password = data.get('password')
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    otp_code_new = randint(1000, 9999)
    otp = OTP.objects.create(user=user, code=otp_code_new)
    user.set_password(password)
    user.save()
    return Response({"otp_key": str(otp.key), 'otp_code': str(otp_code_new)}, status=status.HTTP_201_CREATED)





@swagger_auto_schema(
    methods=['POST'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['key', 'otp_code'],
        properties={
            'key': openapi.Schema(type=openapi.TYPE_STRING, description='OTP kaliti'),
            'otp_code': openapi.Schema(type=openapi.TYPE_STRING, description='OTP kodi')
        }
    ),
    responses={
        200: openapi.Response(
            description="OTP muvaffaqiyatli tasdiqlandi",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Muvaffaqiyatli xabar')
                }
            )
        ),
        400: "Noto'g'ri so'rov",
        404: "OTP topilmadi"
    },
    operation_description="OTP kodini tasdiqlash",
    tags=['auth']
)
@api_view(http_method_names=['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    data = request.data
    serializer = OTPSerializer(data=data)
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    otp = OTP.objects.filter(key=data['key']).first()
    if not otp:
        return Response({"error": "OTP topilmadi"}, status=status.HTTP_404_NOT_FOUND)
    if int(otp.code) != int(data['otp_code']):
        return Response({"error": "OTP noto'g'ri"}, status=status.HTTP_400_BAD_REQUEST)
    if timezone.now() - otp.created_at > timedelta(seconds=180):
        return Response(data={"error": "Sizning OTP vaqtingiz tugadi, iltimos yangi so'rov bering!"}, status=status.HTTP_400_BAD_REQUEST)
    otp.user.is_verify = True
    otp.user.save()
    otp.delete()
    return Response({"message": "OTP tasdiqlandi"}, status=status.HTTP_200_OK)




@swagger_auto_schema(
    methods=['PATCH'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['old_password', 'new_password', 'confirm_password'],
        properties={
            'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='Joriy parol'),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='Yangi parol'),
            'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='Yangi parolni tasdiqlash')
        }
    ),
    responses={
        200: openapi.Response(
            description="Parol muvaffaqiyatli yangilandi",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Muvaffaqiyatli xabar')
                }
            )
        ),
        400: "Noto'g'ri so'rov",
        401: "Avtorizatsiya talab qilinadi"
    },
    operation_description="Foydalanuvchi parolini yangilash",
    tags=['auth']
)
@api_view(http_method_names=['PATCH'])
@permission_classes([IsAuthenticated])
def update_password(request):
    user = request.user
    data = request.data
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    if not user.check_password(old_password):
        return Response({'error': "Eski parol noto'g'ri"}, status=status.HTTP_400_BAD_REQUEST)
    if new_password != confirm_password:
        return Response({'error': 'Yangi parol tasdiqlash paroli bilan teng emas'}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(new_password)
    user.save()
    return Response({'message': 'Muvaffaqiyatli'}, status=status.HTTP_200_OK)





@swagger_auto_schema(
    methods=['POST'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Parol')
        }
    ),
    responses={
        200: openapi.Response(
            description="Kirish muvaffaqiyatli",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Yangilash tokeni'),
                    'access': openapi.Schema(type=openapi.TYPE_STRING, description='Kirish tokeni')
                }
            )
        ),
        401: "Noto'g'ri ma'lumotlar",
        403: "Hisob tasdiqlanmagan"
    },
    operation_description="Foydalanuvchi kirishi",
    tags=['auth']
)
@api_view(http_method_names=['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if not user:
        return Response({'message': "Noto'g'ri username yoki parol"}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_verify:
        return Response({'message': 'Hisob tasdiqlanmagan. Iltimos OTP ni tasdiqlang.'}, status=status.HTTP_403_FORBIDDEN)
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    return Response({'refresh': str(refresh), 'access': str(access_token)}, status=status.HTTP_200_OK)




@swagger_auto_schema(
    methods=['POST'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['phone'],
        properties={
            'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Telefon raqami (+998xxxxxxxxx)')
        }
    ),
    responses={
        200: openapi.Response(
            description="Parol tiklash OTP yuborildi",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Muvaffaqiyatli xabar'),
                    'otp': openapi.Schema(type=openapi.TYPE_INTEGER, description='OTP kodi')
                }
            )
        ),
        400: "Noto'g'ri so'rov",
        401: "Avtorizatsiya talab qilinadi",
        404: "Foydalanuvchi topilmadi"
    },
    operation_description="Parol tiklash OTP so'rash",
    tags=['auth']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_password(request):
    if not request.user.is_authenticated:
         return Response({"message": "Avtorizatsiya talab qilinadi"}, status=status.HTTP_401_UNAUTHORIZED)
    phone = request.data.get('phone')
    if not phone:
        return Response({"message": "Telefon raqami talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return Response({"message": "Noto'g'ri ma'lumotlar"}, status=status.HTTP_404_NOT_FOUND)
    otp_code = randint(100000, 999999)
    OTP.objects.create(user=user, code=otp_code)
    return Response({"message": "Parol tiklash uchun OTP yuborildi", "otp": otp_code}, status=status.HTTP_200_OK)



def register_view(request):
    context = {}
    if request.method == 'POST':
        phone = request.POST.get('phone')
        username = request.POST.get('username')
        password = request.POST.get('password')
        data = {'phone': phone, 'username': username, 'password': password}
        api_url = request.build_absolute_uri('/auth/signup/')
        resp = requests.post(api_url, json=data)
        if User.objects.filter(phone_number=phone, is_verify=True).exists():
            return Response({'error': 'Bu nomer bilan tasdiqlangan akkaunt mavjud'}, status=400)
        if resp.status_code == 201:
            result = resp.json()
            otp_key = result.get('otp_key')
            otp_code = result.get('otp_code')
            return redirect(f'/auth/web-verify/?otp_key={otp_key}&otp_code={otp_code}')
        else:
            try:
                context['error'] = resp.json()
            except Exception:
                context['error'] = resp.text
    return render(request, 'accounts/register.html', context)

def verify_view(request):
    error = None
    otp_key = request.GET.get('otp_key') or request.POST.get('otp_key')
    otp_code = request.GET.get('otp_code')
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        from .models import OTP
        otp = OTP.objects.filter(key=otp_key).first()
        if not otp:
            error = 'OTP topilmadi.'
        elif str(otp.code) != str(otp_code):
            error = "OTP noto'g'ri."
        else:
            user = otp.user
            user.is_verify = True
            user.save()
            otp.delete()
            return redirect('web_login')
    return render(request, 'accounts/verify.html', {'otp_key': otp_key, 'otp_code': otp_code, 'error': error})

def login_view(request):
    context = {}
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        data = {'username': username, 'password': password}
        api_url = request.build_absolute_uri('/auth/login/')
        resp = requests.post(api_url, json=data)
        if resp.status_code == 200:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                django_login(request, user)
                return redirect('my_files_page')
        else:
            try:
                context['error'] = resp.json()
            except Exception:
                context['error'] = resp.text
    return render(request, 'accounts/login.html', context)

def logout_view(request):
    logout(request)
    return redirect('web_login')