# FileShare API – Maxfiy fayllar almashinuvi

**Vazifasi:** Fayl yuklash, maxsus URL orqali boshqalarga yuborish.

## Xususiyatlar

- Fayl yuklash va maxsus link yaratish
- JWT autentifikatsiya
- Fayl yuklovchilar uchun hisobotlar
- IP manzil va kirish vaqtini kuzatish
- berilgan voxtdam keyin avtomatik o'chirish

## Texnik talablar

- Python 3.8+
- Django 5.2+
- Django REST Framework
- JWT autentifikatsiya
- Celery (avtomatik o'chirish uchun)

## API Endpointlar

### Autentifikatsiya (Auth)
- `POST /auth/signup/` — Foydalanuvchini ro'yxatdan o'tkazish (telefon va parol)
- `POST /auth/login/` — Login (username yoki telefon va parol)
- `POST /auth/verify-otp/` — OTP orqali akkauntni tasdiqlash
- `POST /auth/resend-otp/` — OTP kodini qayta yuborish
- `PATCH /auth/update-password/` — Parolni yangilash (eski va yangi parol)
- `POST /auth/reset-password/` — Parolni tiklash uchun OTP yuborish (telefon)
- `POST /auth/confirm-reset-password/` — OTP va yangi parol orqali parolni tiklash

### Fayllar (Files)
- `POST /file/` — Yangi fayl yuklash (expire_hours bilan)
- `GET /file/<link>/` — Faylni unikal link orqali yuklab olish
- `GET /my-files/` — Foydalanuvchining barcha fayllari va loglari

### Web Endpoints (foydalanuvchi interfeysi)
- `/auth/web-register/` — Web orqali ro'yxatdan o'tish
- `/auth/web-login/` — Web orqali login
- `/auth/web-verify/` — Web orqali OTP tasdiqlash
- `/auth/web-update-password/` — Web orqali parolni o'zgartirish
- `/auth/web-forgot-password/` — Web orqali parolni tiklash (telefon)
- `/auth/web-confirm-reset-password/` — Web orqali OTP va yangi parol kiritish

**Fayllar uchun web:**
- `/web/upload/` — Fayl yuklash sahifasi
- `/web/my-files/` — Mening fayllarim (fayllar ro'yxati va loglari)
- `/web/file/<link>/` — Faylni ko'rish va yuklab olish (unikal link orqali)

### Qo'shimcha
- Barcha OTP kodlar Telegramga yuboriladi (web va API uchun)
- Swagger dokumentatsiya: `/swagger/`
- JWT orqali autentifikatsiya (Bearer token)

**Swagger uchun:**
- Avtorizatsiya: Bearer `<access_token>`
- Barcha endpointlar uchun Uzbek tilida javoblar va xatoliklar

