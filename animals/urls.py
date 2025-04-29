from django.urls import path
from . import views

app_name = 'animals'

urlpatterns = [
    # Jenis Hewan URLs
    path('jenis-hewan/', views.jenis_hewan_list, name='jenis_hewan_list'),
    path('jenis-hewan/tambah/', views.jenis_hewan_create, name='jenis_hewan_create'),
    path('jenis-hewan/edit/<uuid:id>/', views.jenis_hewan_update, name='jenis_hewan_update'),
    path('jenis-hewan/hapus/<uuid:id>/', views.jenis_hewan_delete, name='jenis_hewan_delete'),
    path('jenis-hewan/konfirmasi-hapus/<uuid:id>/', views.jenis_hewan_confirm_delete, name='jenis_hewan_confirm_delete'),
    
    # Hewan Peliharaan URLs
    path('hewan/', views.hewan_list, name='hewan_list'),
    path('hewan/tambah/', views.hewan_create, name='hewan_create'),
    path('hewan/edit/<str:nama>/<uuid:no_identitas_klien>/', views.hewan_update, name='hewan_update'),
    path('hewan/hapus/<str:nama>/<uuid:no_identitas_klien>/', views.hewan_delete, name='hewan_delete'),
    path('hewan/konfirmasi-hapus/<str:nama>/<uuid:no_identitas_klien>/', views.hewan_confirm_delete, name='hewan_confirm_delete'),
]