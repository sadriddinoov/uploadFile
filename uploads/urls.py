from django.urls import path
from .views import create_file, my_files, get_file_by_link


urlpatterns = [
    path('upload/', create_file, name='create_file'),
    path('my-files/', my_files, name='my_files'),
    path('file/<str:link>/', get_file_by_link, name='get_file_by_link'),
] 