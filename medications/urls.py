from django.urls import path
from . import views

app_name = 'medications'

urlpatterns = [
    # Medicine management routes
    path('list/', views.medicine_list, name='list'),
    path('add/', views.add_medicine, name='add'),
    path('update/<str:kode>/', views.update_medicine, name='update'),
    path('update_stock/<str:kode>/', views.update_stock, name='update_stock'),
    path('delete/<str:kode>/', views.delete_medicine, name='delete'),
    
    path('prescription/list/', views.prescription_list, name='prescription_list'),
    path('prescription/add/', views.add_prescription, name='add_prescription'),
    path('prescription/delete/', views.delete_prescription, name='delete_prescription'),

    path('my-prescriptions/', views.client_prescription, name='client_prescriptions')
]