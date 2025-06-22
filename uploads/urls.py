from django.urls import path
from .views import create_file, my_files, get_file_by_link, upload_file_page, my_files_page, download_file_page


urlpatterns = [
    path('upload/', create_file, name='create_file'),
    path('my-files/', my_files, name='my_files'),
    path('file/<str:link>/', get_file_by_link, name='get_file_by_link'),
    path('web/upload/', upload_file_page, name='upload_file_page'),
    path('web/my-files/', my_files_page, name='my_files_page'),
    path('web/file/<str:link>/', download_file_page, name='download_file_page'),
] 