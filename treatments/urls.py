
from django.urls import path
from . import views

app_name = 'treatments'

urlpatterns = [
    path('', views.treatment_type_list, name='treatment_type_list'),
    path('add/', views.add_treatment_type, name='add_treatment_type'),
    path('update/<str:kode_perawatan>/', views.update_treatment_type, name='update_treatment_type'),
    path('delete/<str:kode_perawatan>/', views.delete_treatment_type, name='delete_treatment_type'),
]