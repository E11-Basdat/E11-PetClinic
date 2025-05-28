# urls.py
from django.urls import path
from . import views

app_name = 'visits'

urlpatterns = [
    path('', views.visit_list_fd, name='list'),
    path('create/', views.create_visit, name='create_visit'),
    path('update/<str:visit_id>/', views.update_visit, name='update_visit'),
    path('delete/', views.delete_visit, name='delete_visit'),
    path('record/create/', views.create_record, name='create_record'),
    path('record/update/', views.update_record, name='update_record'),
    path('record/get/', views.get_medical_record, name='get_medical_record'),
    path('doctor/', views.doctor_view, name='doctor_view'),
    path('front-desk/', views.visit_list_fd, name='front_desk_view'),
    path('client/', views.client_view, name='client_view'),
    
    # API endpoints
    path('api/perawatan/', views.get_perawatan_options, name='get_perawatan_options'),
    path('get-animals/', views.get_animals_by_client, name='get_animals'),
]