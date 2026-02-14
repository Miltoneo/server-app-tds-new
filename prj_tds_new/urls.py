"""
URL Configuration for prj_tds_new project.
"""
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect


urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),
    
    # TODO: Adicionar URLs do tds_new após criar views
    # path('', include(('tds_new.urls', 'tds_new'), namespace='tds_new')),
    
    # Django Select2 (para widgets de seleção)
    path('select2/', include("django_select2.urls")),
    
    # Redirecionar raiz temporariamente para admin
    path('', lambda request: redirect('admin/', permanent=False)),
]
