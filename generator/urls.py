from django.urls import path
from . import views

urlpatterns = [
    path('', views.generate_questions, name='generate_questions'),
    path('download/<str:file_name>/', views.download_csv, name='download_csv'),
    path('view/<str:csv_file_name>/', views.view_questions, name='view_questions'),
    path('edit/<str:csv_file_name>/', views.edit_questions, name='edit_questions'),
    path('use-questions/<str:csv_file_name>/', views.use_questions, name='use_questions'),
]
