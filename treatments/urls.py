
from django.urls import path
from . import views

app_name = 'treatments'

urlpatterns = [
    path('n_treatment_list', views.n_treatment_list, name='n_treatment_list'),
    path('n_delete/<str:kunjungan_id>/', views.n_delete_treatment, name='n_delete_treatment'),
    path('klien', views.n_treatment_list_klien, name='n_treatment_list_klien'),
    path('doctor', views.n_treatment_list_doctor, name='n_treatment_list_doctor'),
    path('create/', views.n_create_treatment, name='n_create_treatment'),
    path('n_update/<str:kunjungan_id>/', views.n_update_treatment, name='n_update_treatment'),
    path('', views.treatment_type_list, name='treatment_type_list'),
    path('add/', views.add_treatment_type, name='add_treatment_type'),
    path('update/<str:kode_perawatan>/', views.update_treatment_type, name='update_treatment_type'),
    path('delete/<str:kode_perawatan>/', views.delete_treatment_type, name='delete_treatment_type'),
]