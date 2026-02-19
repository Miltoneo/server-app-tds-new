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
from .views import gateway, dispositivo, telemetria
from .views.admin import dashboard as admin_dashboard, provisionamento as admin_prov
from .views.api import provisionamento as api_prov

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
    # TELEMETRIA (Week 10 - Fase 4 Dashboard)
    # =============================================================================
    path('telemetria/', telemetria.telemetria_dashboard, name='telemetria_dashboard'),
    path('telemetria/api/timeline/', telemetria.telemetria_api_grafico_timeline, name='telemetria_api_timeline'),
    path('telemetria/api/barras/', telemetria.telemetria_api_grafico_barras, name='telemetria_api_barras'),
    path('telemetria/api/leituras/', telemetria.telemetria_api_ultimas_leituras, name='telemetria_api_leituras'),
    
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
    
    # Provisionamento - Alocar via Certificado
    path('admin-sistema/provisionamento/certificado/<int:certificado_id>/alocar/',
         admin_prov.alocar_gateway_por_certificado_view,
         name='admin_alocar_gateway_por_certificado'),

    # Provisionamento - Geração de Certificado (modo factory)
    path('admin-sistema/provisionamento/gateway/<int:gateway_id>/gerar-certificado/',
         admin_prov.gerar_certificado_gateway_view,
         name='admin_gerar_certificado_gateway'),

    # Provisionamento - Download do pacote ZIP de provisionamento
    path('admin-sistema/provisionamento/certificado/<int:certificado_id>/download/',
         admin_prov.download_certificado_zip_view,
         name='admin_download_certificado'),

    # Provisionamento - Revogação de Certificado
    path('admin-sistema/provisionamento/certificado/<int:certificado_id>/revogar/',
         admin_prov.revogar_certificado_view,
         name='admin_revogar_certificado'),

    # -------------------------------------------------------------------------
    # Bootstrap Certificates — cert compartilhado para a fábrica
    # -------------------------------------------------------------------------
    path('admin-sistema/provisionamento/bootstrap/',
         admin_prov.bootstrap_cert_list_view,
         name='admin_bootstrap_list'),

    path('admin-sistema/provisionamento/bootstrap/gerar/',
         admin_prov.gerar_bootstrap_cert_view,
         name='admin_gerar_bootstrap'),

    path('admin-sistema/provisionamento/bootstrap/<int:bootstrap_id>/download/',
         admin_prov.download_bootstrap_zip_view,
         name='admin_download_bootstrap'),

    path('admin-sistema/provisionamento/bootstrap/<int:bootstrap_id>/revogar/',
         admin_prov.revogar_bootstrap_cert_view,
         name='admin_revogar_bootstrap'),

    # -------------------------------------------------------------------------
    # Registros Pendentes — devices que fizeram auto-registro no primeiro boot
    # -------------------------------------------------------------------------
    path('admin-sistema/provisionamento/registros/',
         admin_prov.registros_pendentes_view,
         name='admin_registros_pendentes'),

    path('admin-sistema/provisionamento/registros/<int:registro_id>/processar/',
         admin_prov.processar_registro_view,
         name='admin_processar_registro'),

    path('admin-sistema/provisionamento/registros/<int:registro_id>/rejeitar/',
         admin_prov.rejeitar_registro_view,
         name='admin_rejeitar_registro'),

    # -------------------------------------------------------------------------
    # API REST — endpoint chamado pelo device no primeiro boot
    # -------------------------------------------------------------------------
    path('api/provision/register/',
         api_prov.auto_register_view,
         name='api_auto_register'),
    
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
