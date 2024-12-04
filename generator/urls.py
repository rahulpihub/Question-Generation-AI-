from django.urls import path
from . import views

urlpatterns = [
    path('', views.generate_questions, name='generate_questions'),
    path('download_csv/<str:file_name>/', views.download_csv, name='download_csv'),
]
