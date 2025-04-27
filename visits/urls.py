from django.urls import path
from . import views

app_name = 'visits'  # Pastikan namespace ini sesuai

urlpatterns = [
    path('', views.list_visits, name='list_visits'),
    path('create/', views.create_visit, name='create_visit'),
    path('update/<str:visit_id>/', views.update_visit, name='update_visit'),
    path('delete/<str:visit_id>/', views.delete_visit, name='delete_visit'),
    path('medical-records/create/<str:id_kunjungan>/', views.create_medical_record, name='create_medical_record'),
    path('check-medical-record/<str:id_kunjungan>/', views.check_medical_record, name='check_medical_record'),
]