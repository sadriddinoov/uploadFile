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

## O'rnatish

1. Loyihani yuklab oling:
```bash
git clone <repository-url>
cd fileshare
```

2. Virtual muhitni yarating va faollashtiring:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac uchun
# yoki
venv\Scripts\activate  # Windows uchun
```

3. Kerakli kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

4. Ma'lumotlar bazasini sozlang:
```bash
python manage.py migrate
```

5. Superuser yarating:
```bash
python manage.py createsuperuser
```

6. Dasturni ishga tushiring:
```bash
python manage.py runserver
```

## API Endpointlar

### Autentifikatsiya
- `POST /api/token/` - JWT token olish
- `POST /api/token/refresh/` - Token yangilash

### Fayllar
- `POST /api/files/` - Yangi fayl yuklash
- `GET /api/files/` - Fayllar ro'yxatini ko'rish
- `GET /api/files/{id}/` - Fayl haqida ma'lumot
- `POST /api/files/{id}/generate-link/` - Yangi link yaratish
- `GET /api/files/{id}/download/` - Faylni yuklab olish
- `GET /api/files/{id}/stats/` - Fayl statistikasi

