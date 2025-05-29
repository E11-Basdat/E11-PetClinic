from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('', views.show_pengguna, name='pengguna'),
    path('login/', views.login_user, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-password/', views.update_password, name='update_password'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('list-client/', views.list_client, name='list_client'),
    path('client-detail/<str:no_identitas>/', views.client_detail, name='client_detail'),
    path('my-data/', views.my_client_data, name='my_client_data'),
]
