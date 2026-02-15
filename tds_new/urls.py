"""
URL Configuration para o app tds_new.

Padrões de nomenclatura (conforme guia):
- path e name em snake_case
- Incluir todos os parâmetros de contexto necessários
- Usar namespace 'tds_new' para isolamento

Criado em: 14/02/2026
"""
from django.urls import path
from . import views

app_name = 'tds_new'

urlpatterns = [
    # =============================================================================
    # AUTENTICAÇÃO
    # =============================================================================
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/select-account/', views.select_account_view, name='select_account'),
    path('auth/license-expired/', views.license_expired_view, name='license_expired'),
    
    # =============================================================================
    # DASHBOARD
    # =============================================================================
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
    
    # =============================================================================
    # CENÁRIOS (Navegação Principal)
    # =============================================================================
    path('cenario/home/', views.cenario_home, name='cenario_home'),
    path('cenario/dispositivos/', views.cenario_dispositivos, name='cenario_dispositivos'),
    path('cenario/telemetria/', views.cenario_telemetria, name='cenario_telemetria'),
    path('cenario/alertas/', views.cenario_alertas, name='cenario_alertas'),
    path('cenario/relatorios/', views.cenario_relatorios, name='cenario_relatorios'),
    path('cenario/configuracoes/', views.cenario_configuracoes, name='cenario_configuracoes'),
    path('cenario/conta/', views.cenario_conta, name='cenario_conta'),
    path('cenario/usuarios/', views.cenario_usuarios, name='cenario_usuarios'),
    
    # =============================================================================
    # TODO: Adicionar URLs específicas nas próximas weeks
    # =============================================================================
    # Week 6-7: Dispositivos IoT
    # path('dispositivos/', views.dispositivo_list, name='dispositivo_list'),
    # path('dispositivos/novo/', views.dispositivo_create, name='dispositivo_create'),
    # path('dispositivos/<int:pk>/editar/', views.dispositivo_update, name='dispositivo_update'),
    # path('dispositivos/<int:pk>/excluir/', views.dispositivo_delete, name='dispositivo_delete'),
    
    # Week 8-9: Telemetria e Alertas
    # path('telemetria/', views.telemetria_dashboard, name='telemetria_dashboard'),
    # path('telemetria/<int:dispositivo_id>/', views.telemetria_detail, name='telemetria_detail'),
    # path('alertas/', views.alerta_list, name='alerta_list'),
    # path('alertas/<int:pk>/', views.alerta_detail, name='alerta_detail'),
    
    # Week 10: Relatórios
    # path('relatorios/', views.relatorio_list, name='relatorio_list'),
    # path('relatorios/<str:tipo>/', views.relatorio_generate, name='relatorio_generate'),
]
