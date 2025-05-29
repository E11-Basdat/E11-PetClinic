# medications/urls.py
from django.urls import path
from . import views

app_name = 'medications'

urlpatterns = [
    path('', views.medicine_list, name='medicine_list'),
    path('add/', views.add_medicine, name='add_medicine'),
    path('update/<str:medicine_id>/', views.update_medicine, name='update_medicine'),
    path('update-stock/<str:medicine_id>/', views.update_medicine_stock, name='update_medicine_stock'),
    path('delete/<str:medicine_id>/', views.delete_medicine, name='delete_medicine'),
    
    # # Prescription management
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/add/', views.add_prescription, name='add_prescription'),
    path('prescription/delete/<str:kode_perawatan>/<str:kode_obat>/', views.delete_prescription, name='delete_prescription'),
    # Optional: AJAX version
    path('prescription/delete-ajax/<str:kode_perawatan>/<str:kode_obat>/', views.delete_prescription_ajax, name='delete_prescription_ajax'),
]