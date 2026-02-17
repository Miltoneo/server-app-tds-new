"""
URL Configuration for prj_tds_new project.
"""
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect


urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),
    
    # Redirect raiz para app
    path('', lambda request: redirect('tds_new:dashboard')),
    
    # App TDS New (Week 4-5)
    path('tds_new/', include(('tds_new.urls', 'tds_new'), namespace='tds_new')),
    
    # Django Select2 (para widgets de seleção)
    path('select2/', include("django_select2.urls")),
]
