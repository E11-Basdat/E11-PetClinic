"""
URL configuration for petclinic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from visits import views as visit_views
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('animals/', include('animals.urls')),
    path('medications/', include('medications.urls')),
    path('vaccinations/', include('vaccinations.urls')),
    path('visits/', include('visits.urls')),
    path('treatments/', include('treatments.urls')),
    path('client-prescription/', include('client_prescription.urls')),
    path('get-animals/', visit_views.get_animals, name='get_animals'),
]
