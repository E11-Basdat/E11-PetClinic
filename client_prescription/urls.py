from django.urls import path
from . import views

app_name = 'client_prescription'

urlpatterns = [
    path('prescription/', views.client_prescription, name='client_prescription'),
    path('api/prescription-summary/', views.get_prescription_summary, name='prescription_summary'),
]