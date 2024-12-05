from django.urls import path
from . import views

urlpatterns = [
    path('', views.generate_questions, name='generate_questions'),
    path('download/<str:file_name>/', views.download_csv, name='download_csv'),
    path('view/<str:csv_file_name>/', views.view_questions, name='view_questions'),
]
