from django.urls import path
from . import views

app_name = 'treatments'

urlpatterns = [
    path('', views.treatment_list, name='treatment_list'),
    path('create/', views.create_treatment, name='create_treatment'),
    path('update/<str:kunjungan_id>/', views.update_treatment, name='update_treatment'),
    path('delete/<str:kunjungan_id>/', views.delete_treatment, name='delete_treatment'),
]

# urlpatterns = [
#     path('', views.list_treatments, name='list_treatments'),
#     path('create/', views.create_treatment, name='create_treatment'),
#     path('update/<str:kunjungan_id>/<str:kode_perawatan>/', views.update_treatment, name='update_treatment'),
#     path('delete/<str:kunjungan_id>/<str:kode_perawatan>/', views.delete_treatment, name='delete_treatment'),
# ]

