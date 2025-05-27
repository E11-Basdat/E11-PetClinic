from django.urls import path
from . import views

urlpatterns = [
    path('list-vaccinations/', views.vaccination_list, name='vaccination_list'),
    path('add-vaccination/', views.add_vaccination, name='add_vaccination'),
    path('update-vaccination/<str:id_kunjungan>/', views.update_vaccination, name='update_vaccination'),
    path('delete-vaccination/<str:id_kunjungan>/', views.delete_vaccination, name='delete_vaccination'),
    path('list-vaccines/', views.vaccine_list, name='vaccine_list'),
    path('add-vaccine/', views.add_vaccine, name='add_vaccine'),
    path('update-vaccine/<str:kode>/', views.update_vaccine, name='update_vaccine'),
    path('update-stock/<str:kode>/', views.update_stock, name='update_stock'),
    path('check-vaccine-delete/<str:kode>/', views.check_vaccine_delete, name='check_vaccine_delete'),
    path('delete-vaccine/<str:kode>/', views.delete_vaccine, name='delete_vaccine'),
    path('client/', views.client_vaccination_list, name='client_vaccination_list'),
]


