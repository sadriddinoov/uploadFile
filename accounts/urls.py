from django.urls import path
from . import views


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('update-password/', views.update_password, name='update_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('confirm-reset-password', views.confirm_reset_password, name='reset_password_confirmation'),
    path('web-register/', views.register_view, name='web_register'),
    path('web-login/', views.login_view, name='web_login'),
    path('web-verify/', views.verify_view, name='web_verify'),
    path('logout/', views.logout_view, name='logout'),
    path('web-update-password/', views.web_update_password, name='web_update_password'),
    path('web-forgot-password/', views.web_forgot_password, name='web_forgot_password'),
    path('web-confirm-reset-password/', views.web_confirm_reset_password, name='web_confirm_reset_password'),
] 