from django.urls import path
from . import views

app_name = 'treatments'

urlpatterns = [ 
    # ----------------------------- NIA -----------------------------------
    path('', views.n_treatment_list, name='n_treatment_list'),
    path('create/', views.n_create_treatment, name='n_create_treatment'),
    path('update/<str:kunjungan_id>/', views.n_update_treatment, name='n_update_treatment'),
    path('delete/<str:kunjungan_id>/', views.n_delete_treatment, name='n_delete_treatment'),
    
# ---------------------------------------------------Batas Wilayah -------------------------------------------
# ---------------------------------------------------Batas Wilayah -------------------------------------------
# ---------------------------------------------------Batas Wilayah -------------------------------------------
    
    
    path('treatments/', views.treatment_list, name='treatment_list'),
]


