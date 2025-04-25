
from django.urls import path
from . import views

app_name = 'medications'

urlpatterns = [
    # Original medicine routes
    path('list/', views.medicine_list, name='list'),
    path('add/', views.add_medicine, name='add'),
    path('update/<str:code>/', views.update_medicine, name='update'),
    path('stock/<str:code>/', views.update_stock, name='update_stock'),
    path('delete/<str:code>/', views.delete_medicine, name='delete'),
    
    # New treatment routes
    path('treatments/', views.treatment_list, name='treatment_list'),
    path('treatments/add/', views.add_treatment, name='add_treatment'),
    path('treatments/update/', views.update_treatment, name='update_treatment'),
    path('treatments/delete/', views.delete_treatment, name='delete_treatment'),
]