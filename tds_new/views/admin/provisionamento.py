"""
Gestão de provisionamento - Gateways e Certificados
Week 8: Lista global de certificados

Week 9 (planejado):
- Alocação de gateways entre contas
- Importação em lote via CSV
- Revogação de certificados
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone

from tds_new.models import CertificadoDevice


class CertificadosListView(UserPassesTestMixin, ListView):
    """
    Lista global de certificados X.509 de todos os gateways
    
    Diferença da view usuário final:
    - Usuário final: vê apenas certificados da sua conta
    - Admin: vê certificados de TODAS as contas
    
    Filtros disponíveis:
    - validos: Certificados não revogados e não expirados
    - expirados: Certificados com expires_at < now()
    - revogados: Certificados com is_revoked=True
    """
    model = CertificadoDevice
    template_name = 'admin_sistema/provisionamento/certificados_list.html'
    context_object_name = 'certificados'
    paginate_by = 50
    
    def test_func(self):
        """Apenas staff members podem acessar"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        """
        IMPORTANTE: Não filtrar por conta (visão global)
        Esta é a diferença fundamental entre view admin e view de usuário final
        """
        queryset = CertificadoDevice.objects.select_related('conta').order_by('-created_at')
        
        # Filtros opcionais via GET
        status = self.request.GET.get('status')
        if status == 'validos':
            queryset = queryset.filter(
                is_revoked=False,
                expires_at__gt=timezone.now()
            )
        elif status == 'expirados':
            queryset = queryset.filter(expires_at__lt=timezone.now())
        elif status == 'revogados':
            queryset = queryset.filter(is_revoked=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Certificados do Sistema - Visão Global'
        
        # Estatísticas para filtros
        context['total_validos'] = CertificadoDevice.objects.filter(
            is_revoked=False,
            expires_at__gt=timezone.now()
        ).count()
        context['total_expirados'] = CertificadoDevice.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        context['total_revogados'] = CertificadoDevice.objects.filter(
            is_revoked=True
        ).count()
        
        return context


# =============================================================================
# Week 9: Funções de provisionamento (planejadas)
# =============================================================================

# @staff_member_required
# def alocar_gateway_view(request, gateway_id):
#     """Aloca gateway a uma conta específica"""
#     pass

# class ImportarGatewaysCSVView(UserPassesTestMixin, FormView):
#     """Importa gateways em lote via arquivo CSV"""
#     pass

# @staff_member_required
# def revogar_certificado_view(request, certificado_id):
#     """Revoga um certificado X.509"""
#     pass
