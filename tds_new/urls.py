"""
URL Configuration para o app tds_new.

Padrões de nomenclatura (conforme guia):
- path e name em snake_case
- Incluir todos os parâmetros de contexto necessários
- Usar namespace 'tds_new' para isolamento

Criado em: 14/02/2026
Atualizado em: 17/01/2026 (Week 6-7 - Dispositivos IoT)
Atualizado em: 17/02/2026 (Week 8 - Admin Sistema)
"""
from django.urls import path
from . import views
from .views import gateway, dispositivo
from .views.admin import dashboard as admin_dashboard, provisionamento as admin_prov

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
    # GATEWAYS (Week 6-7)
    # =============================================================================
    path('gateways/', gateway.GatewayListView.as_view(), name='gateway_list'),
    path('gateways/novo/', gateway.GatewayCreateView.as_view(), name='gateway_create'),
    path('gateways/<int:pk>/', gateway.GatewayDetailView.as_view(), name='gateway_detail'),
    path('gateways/<int:pk>/editar/', gateway.GatewayUpdateView.as_view(), name='gateway_edit'),
    path('gateways/<int:pk>/excluir/', gateway.GatewayDeleteView.as_view(), name='gateway_delete'),
    
    # =============================================================================
    # DISPOSITIVOS (Week 6-7)
    # =============================================================================
    path('dispositivos/', dispositivo.DispositivoListView.as_view(), name='dispositivo_list'),
    path('dispositivos/novo/', dispositivo.DispositivoCreateView.as_view(), name='dispositivo_create'),
    path('dispositivos/<int:pk>/', dispositivo.DispositivoDetailView.as_view(), name='dispositivo_detail'),
    path('dispositivos/<int:pk>/editar/', dispositivo.DispositivoUpdateView.as_view(), name='dispositivo_edit'),
    path('dispositivos/<int:pk>/excluir/', dispositivo.DispositivoDeleteView.as_view(), name='dispositivo_delete'),
    
    # =============================================================================
    # ADMIN SISTEMA (Super Admin Only) - Week 8
    # =============================================================================
    
    # Dashboard Global
    path('admin-sistema/', 
         admin_dashboard.dashboard_global, 
         name='admin_dashboard'),
    
    # Provisionamento - Certificados
    path('admin-sistema/provisionamento/certificados/', 
         admin_prov.CertificadosListView.as_view(), 
         name='admin_certificados_list'),
    
    # Provisionamento - Alocação de Gateways (Week 9 - Fase 1)
    path('admin-sistema/provisionamento/alocar/<int:gateway_id>/',
         admin_prov.alocar_gateway_view,
         name='admin_alocar_gateway'),
    
    # Provisionamento - Alocar via Certificado (Week 9 - Fase 1)
    path('admin-sistema/provisionamento/certificado/<int:certificado_id>/alocar/',
         admin_prov.alocar_gateway_por_certificado_view,
         name='admin_alocar_gateway_por_certificado'),
    
    # Week 9 (planejado): Importação CSV, revogação
    # path('admin-sistema/provisionamento/importar-csv/', ...)
    # path('admin-sistema/provisionamento/certificados/<int:certificado_id>/revogar/', ...)
    
    # Week 9 (planejado): Auditoria
    # path('admin-sistema/auditoria/logs/', ...)
    # path('admin-sistema/auditoria/certificados-revogados/', ...)
    
    # =============================================================================
    # TODO: Adicionar URLs específicas nas próximas weeks
    # =============================================================================
    # Week 8-9: Telemetria e Alertas
    # path('telemetria/', views.telemetria_dashboard, name='telemetria_dashboard'),
    # path('telemetria/<int:dispositivo_id>/', views.telemetria_detail, name='telemetria_detail'),
    # path('alertas/', views.alerta_list, name='alerta_list'),
    # path('alertas/<int:pk>/', views.alerta_detail, name='alerta_detail'),
    
    # Week 10: Relatórios
    # path('relatorios/', views.relatorio_list, name='relatorio_list'),
    # path('relatorios/<str:tipo>/', views.relatorio_generate, name='relatorio_generate'),
]
