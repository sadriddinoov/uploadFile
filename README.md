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

### Autentifikatsiya
- `POST /auth/signup/` - User registratsiya qilish
- `POST /auth/login/` - User login qilish
- `POST /auth/verify-otp/` - User akkauntini tasdiqlash
- `PUT /auth/update-password/` - User parolini almashtirish
- `POST /auth/reset-password/` - User parolini qayta ornatish

### Fayllar
- `POST /api/files/` - Yangi fayl yuklash
- `GET /api/files/` - Fayllar ro'yxatini ko'rish
- `GET /api/files/{id}/` - Fayl haqida ma'lumot
- `POST /api/files/{id}/generate-link/` - Yangi link yaratish
- `GET /api/files/{id}/download/` - Faylni yuklab olish
- `GET /api/files/{id}/stats/` - Fayl statistikasi

