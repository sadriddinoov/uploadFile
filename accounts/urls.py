from django.urls import path
from . import views


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('update-password/', views.update_password, name='update_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
] 