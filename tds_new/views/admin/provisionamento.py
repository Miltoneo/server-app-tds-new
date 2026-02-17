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
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction

from tds_new.models import CertificadoDevice, Gateway, Dispositivo
from tds_new.forms.provisionamento import AlocarGatewayForm


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
        
        # Week 9: Adicionar gateway relacionado a cada certificado
        # Criar dicionário mac_address -> gateway para lookup rápido
        certificados_list = context['certificados']
        if certificados_list:
            macs = [cert.mac_address for cert in certificados_list]
            gateways_dict = {
                gw.mac: gw 
                for gw in Gateway.objects.filter(mac__in=macs)
            }
            
            # Adicionar gateway a cada certificado
            for cert in certificados_list:
                cert.gateway = gateways_dict.get(cert.mac_address)
        
        return context


# =============================================================================
# Week 9: Funções de provisionamento
# =============================================================================

@staff_member_required
def alocar_gateway_view(request, gateway_id):
    """
    Aloca ou realoca gateway para uma conta específica
    
    Funcionalidades:
    1. Transfere gateway entre contas (ou aloca gateway órfão)
    2. Atualiza certificado X.509 junto com o gateway
    3. Opcionalmente transfere dispositivos vinculados
    4. Valida integridade dos dados (conta ativa, MAC único)
    
    Args:
        gateway_id (int): ID do gateway a ser alocado
    
    Returns:
        HttpResponse: Formulário de alocação ou redirect após sucesso
    
    Fluxo:
    - GET: Exibe formulário com dados do gateway e opções
    - POST: Processa alocação e atualiza registros relacionados
    
    Week 9 - Fase 1: Alocação Manual
    """
    gateway = get_object_or_404(Gateway, pk=gateway_id)
    dispositivos_vinculados = Dispositivo.objects.filter(gateway=gateway)
    
    # Buscar certificado associado ao gateway
    certificado = CertificadoDevice.objects.filter(mac_address=gateway.mac).first()
    
    if request.method == 'POST':
        form = AlocarGatewayForm(request.POST, instance=gateway)
        
        if form.is_valid():
            transferir_dispositivos = form.cleaned_data.get('transferir_dispositivos', False)
            conta_destino = form.cleaned_data['conta']
            conta_origem = gateway.conta  # Pode ser None (gateway órfão)
            
            # Usar transação para garantir atomicidade
            try:
                with transaction.atomic():
                    # 1. Atualizar gateway
                    gateway.conta = conta_destino
                    gateway.save()
                    
                    # 2. Atualizar certificado (se existir)
                    if certificado:
                        certificado.conta = conta_destino
                        certificado.save()
                        messages.success(request, f"✅ Certificado {certificado.serial_number[:16]}... atualizado")
                    else:
                        messages.warning(
                            request,
                            f"⚠️ Gateway sem certificado X.509. "
                            f"Conexão MQTT não funcionará até gerar certificado!"
                        )
                    
                    # 3. Transferir dispositivos vinculados (se marcado)
                    if transferir_dispositivos and dispositivos_vinculados.exists():
                        count_dispositivos = dispositivos_vinculados.count()
                        dispositivos_vinculados.update(conta=conta_destino)
                        messages.info(
                            request,
                            f"📦 {count_dispositivos} dispositivo(s) transferido(s) junto com o gateway"
                        )
                    
                    # Mensagem principal de sucesso
                    if conta_origem:
                        messages.success(
                            request,
                            f"✅ Gateway {gateway.mac} transferido de "
                            f"'{conta_origem.name}' → '{conta_destino.name}'"
                        )
                    else:
                        messages.success(
                            request,
                            f"✅ Gateway {gateway.mac} alocado para '{conta_destino.name}'"
                        )
                    
                    # TODO Week 9.4: Registrar auditoria
                    # LogEntry.objects.log_action(...)
                    
                    return redirect('tds_new:admin_certificados_list')
            
            except Exception as e:
                messages.error(
                    request,
                    f"❌ Erro ao alocar gateway: {str(e)}"
                )
    
    else:
        form = AlocarGatewayForm(instance=gateway)
    
    context = {
        'gateway': gateway,
        'form': form,
        'dispositivos_vinculados': dispositivos_vinculados,
        'certificado': certificado,
        'titulo_pagina': f'Alocar Gateway {gateway.mac}',
    }
    
    return render(request, 'admin_sistema/provisionamento/alocar_gateway.html', context)


@staff_member_required
def alocar_gateway_por_certificado_view(request, certificado_id):
    """
    Ponto de entrada unificado para alocação via certificado
    
    Fluxo:
    1. Busca certificado
    2. Verifica se existe gateway com MAC correspondente
    3. Se existe: redireciona para alocar_gateway_view
    4. Se não existe: mostra template explicativo (sem gateway)
    
    Args:
        certificado_id (int): ID do certificado X.509
    
    Returns:
        HttpResponse ou HttpResponseRedirect
    
    Week 9 - Fase 1: Rota unificada via certificado
    """
    certificado = get_object_or_404(CertificadoDevice, pk=certificado_id)
    
    # Verificar se existe gateway com este MAC
    gateway = Gateway.objects.filter(mac=certificado.mac_address).first()
    
    if gateway:
        # Gateway existe: redirecionar para fluxo normal de alocação
        return redirect('tds_new:admin_alocar_gateway', gateway_id=gateway.id)
    
    # Gateway não existe: mostrar template explicativo
    context = {
        'certificado': certificado,
        'gateway': None,
        'titulo_pagina': f'Certificado sem Gateway - MAC {certificado.mac_address}',
    }
    
    return render(request, 'admin_sistema/provisionamento/alocar_gateway.html', context)


# =============================================================================
# Week 9: Planejado (Fases 2, 3, 4)
# =============================================================================

# class ImportarGatewaysCSVView(UserPassesTestMixin, FormView):
#     """Importa gateways em lote via arquivo CSV"""
#     pass

# @staff_member_required
# def revogar_certificado_view(request, certificado_id):
#     """Revoga um certificado X.509"""
#     pass
