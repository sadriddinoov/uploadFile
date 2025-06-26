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
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings


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
        400: "Invalid credentials"
    },
    operation_description="Yengi foydalanuvchi qo'shish",
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
    otp_code = randint(100000, 999999)
    otp = OTP.objects.create(user=user, code=otp_code)
    otp.save()
    user.set_password(password)
    user.save()
    send_telegram_otp(otp_code)
    return Response({"otp_key": str(otp.key), 'otp_code': str(otp_code)}, status=status.HTTP_201_CREATED)





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
        400: "Invalid credentials",
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
        return Response({"error": "OTP invalid"}, status=status.HTTP_400_BAD_REQUEST)
    if timezone.now() - otp.created_at > timedelta(seconds=180):
        return Response(data={"error": "Sizning OTP vaqtingiz tugadi, iltimos Yengi so'rov bering!"}, status=status.HTTP_400_BAD_REQUEST)
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
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='Yengi parol'),
            'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='Yengi parolni tasdiqlash')
        }
    ),
    responses={
        200: openapi.Response(
            description="Parol muvaffaqiyatli Yengilandi",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Muvaffaqiyatli xabar')
                }
            )
        ),
        400: "Invalid credentials",
        401: "Avtorizatsiya required"
    },
    operation_description="Foydalanuvchi parolini Yengilash",
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
        return Response({'error': "Eski parol invalid"}, status=status.HTTP_400_BAD_REQUEST)
    if new_password != confirm_password:
        return Response({'error': 'Yengi parol tasdiqlash paroli bilan teng emas'}, status=status.HTTP_400_BAD_REQUEST)
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
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Yengilash tokeni'),
                    'access': openapi.Schema(type=openapi.TYPE_STRING, description='Kirish tokeni')
                }
            )
        ),
        401: "invalid ma'lumotlar",
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
        return Response({'message': "invalid username yoki parol"}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_verify:
        return Response({'message': 'Hisob tasdiqlanmagan. Iltimos OTP ni tasdiqlang'}, status=status.HTTP_403_FORBIDDEN)
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
        400: "Invalid credentials",
        401: "Avtorizatsiya required",
        404: "Foydalanuvchi topilmadi"
    },
    operation_description="Parol tiklash OTP so'rash",
    tags=['auth']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_password(request):
    if not request.user.is_authenticated:
         return Response({"message": "Avtorizatsiya required"}, status=status.HTTP_401_UNAUTHORIZED)
    phone = request.data.get('phone')
    if not phone:
        return Response({"message": "Telefon raqami required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(phone_number=phone)
    except User.DoesNotExist:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_404_NOT_FOUND)
    otp_code = randint(100000, 999999)
    otp = OTP.objects.create(user=user, code=otp_code)
    otp.save()
    send_telegram_otp(otp_code, phone)
    return Response({"message": "Parol tiklash uchun OTP yuborildi"}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    methods=['POST'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['otp_code', 'new_password'],
        properties={
            'otp_code': openapi.Schema(type=openapi.TYPE_INTEGER, description='OTP kodi'),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='Yengi parol')
        }
    ),
    responses={
        200: openapi.Response(
            description="Parol muvaffaqiyatli Yengilandi",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Muvaffaqiyatli xabar')
                }
            )
        ),
        400: "Invalid credentials",
        401: "Avtorizatsiya required",
        404: "OTP topilmadi"
    },
    operation_description="OTP va Yengi parol orqali parolni tiklash",
    tags=['auth']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_reset_password(request):
    user = request.user
    otp_code = request.data.get('otp_code')
    new_password = request.data.get('new_password')
    if not otp_code or not new_password:
        return Response({'message': "OTP kodi va Yengi parol kiritilishi shart"}, status=status.HTTP_400_BAD_REQUEST)
    print(user, otp_code)
    otp = OTP.objects.filter(user=user, code=otp_code).first()
    if not otp:
        return Response({'message': "OTP invalid yoki topilmadi"}, status=status.HTTP_404_NOT_FOUND)
    user.set_password(new_password)
    user.save()
    otp.delete()
    return Response({'message': "Parol muvaffaqiyatli Yengilandi"}, status=status.HTTP_200_OK)


# FOR web

def register_view(request):
    context = {}
    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if User.objects.filter(phone_number=phone).exists():
            context['error'] = 'Bu telefon raqami bilan akkaunt mavjud'
            return render(request, 'accounts/register.html', context)

        if User.objects.filter(phone_number=phone, is_verify=True).exists():
            context['error'] = 'Bu nomer bilan tasdiqlangan akkaunt mavjud'
            return render(request, 'accounts/register.html', context)
        
        if User.objects.filter(username=username).exists():
            context['error'] = 'Bu username bilan akkaunt mavjud'
            return render(request, 'accounts/register.html', context)

        user = User.objects.create(
            username=username,
            phone_number=phone,
            is_verify=False
        )
        user.set_password(password)
        user.save()

        otp_code = randint(100000, 999999)
        otp = OTP.objects.create(user=user, code=otp_code)
        otp.save()
        send_telegram_otp(otp_code, phone)
        return redirect(f'/auth/web-verify/?otp_key={otp.key}')

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
            error = 'OTP topilmadi'
        elif str(otp.code) != str(otp_code):
            error = "OTP invalid"
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

@login_required(login_url="/auth/web-login/")
def web_update_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not request.user.check_password(old_password):
            messages.error(request, "Eski parol invalid")
        elif new_password != confirm_password:
            messages.error(request, "Yengi parol tasdiqlashdigi paroli bilan bir xil emas")
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "Parol muvaffaqiyatli o'zgartirildi")
            return redirect('web_update_password')
    return render(request, 'accounts/web_update_password.html')

def web_forgot_password(request):
    context = {}
    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        if not phone:
            context['error'] = 'Telefon raqami kerak'
        else:
            try:
                user = User.objects.get(phone_number=phone)
                if not user.is_verify:
                    context['error'] = 'Bu raqam tasdiqlanmagan'
                else:
                    OTP.objects.filter(user=user).delete()
                    otp_code = randint(100000, 999999)
                    OTP.objects.create(user=user, code=otp_code)
                    send_telegram_otp(otp_code, phone)
                    return redirect(f'/auth/web-confirm-reset-password/?phone_number={phone}')
            except User.DoesNotExist:
                context['error'] = 'Bunday foydalanuvchi topilmadi'
    return render(request, 'accounts/web_forgot_password.html', context)

def web_confirm_reset_password(request):
    context = {}
    phone = request.GET.get('phone_number') or request.POST.get('phone_number')
    if phone:
        phone = str(phone).replace(' ', '')
        if not phone.startswith('+'):
            phone = '+' + phone
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        new_password = request.POST.get('new_password')
        try:
            user = User.objects.get(phone_number=phone)
            otp = OTP.objects.filter(user=user, code=otp_code).first()
            if not otp:
                context['error'] = "OTP invalid yoki topilmadi"
            else:
                user.set_password(new_password)
                user.save()
                otp.delete()
                context['success'] = "Parol muvaffaqiyatli o'zgartirildi"
        except User.DoesNotExist:
            context['error'] = 'Bunday foydalanuvchi topilmadi'
    context['phone_number'] = phone
    return render(request, 'accounts/web_confirm_reset_password.html', context)

def send_telegram_otp(otp_code, phone=None):
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    user_id = getattr(settings, 'TELEGRAM_ADMIN_USER_ID', None)
    if not token or not user_id:
        return
    text = f"New OTP: {otp_code}"
    if phone:
        text += f"\nTelefon: {phone}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": user_id, "text": text}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception:
        pass