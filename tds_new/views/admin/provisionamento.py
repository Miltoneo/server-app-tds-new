"""
Gestão de provisionamento - Gateways e Certificados
Week 8: Lista global de certificados

Week 9: Alocação de gateways, geração/download/revogação de certificados
Week 9+: Bootstrap certificates + Auto-registro de devices
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse

from tds_new.models import CertificadoDevice, Gateway, Dispositivo, BootstrapCertificate, RegistroProvisionamento
from tds_new.forms.provisionamento import (
    AlocarGatewayForm,
    GerarCertificadoFactoryForm,
    RevogarCertificadoForm,
    GerarBootstrapCertForm,
    RevogarBootstrapCertForm,
    ProcessarRegistroForm,
)


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
        queryset = CertificadoDevice.objects.select_related('conta', 'gateway').order_by('-created_at')
        
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
# GERAÇÃO DE CERTIFICADOS
# =============================================================================

@staff_member_required
def gerar_certificado_gateway_view(request, gateway_id):
    """
    Geração de certificado X.509 para um gateway via modo factory.

    Fluxo (modo factory — admin grava fisicamente no dispositivo):
      1. Admin seleciona gateway
      2. Formulário confirma dados (device_id, MAC, conta)
      3. CertificadoService.gerar_certificado_factory() é chamado
      4. Redireciona para download do ZIP de provisionamento

    Para o fluxo CSR (dispositivo envia CSR), ver: sign_csr_api_view (API endpoint)
    """
    from tds_new.services.certificados import CertificadoService, CertificadoServiceError, CertificadoJaExistenteError, CANaoConfiguradaError

    gateway = get_object_or_404(Gateway, pk=gateway_id)

    # Verificar se já existe certificado ativo
    cert_ativo = CertificadoDevice.objects.filter(
        conta=gateway.conta,
        device_id=gateway.device_id,
        is_revoked=False
    ).first() if gateway.device_id else None

    if request.method == 'POST':
        form = GerarCertificadoFactoryForm(request.POST, gateway=gateway)
        if form.is_valid():
            forcar_renovacao = form.cleaned_data.get('forcar_renovacao', False)
            try:
                service = CertificadoService()
                cert = service.gerar_certificado_factory(
                    device_id=gateway.device_id or gateway.mac,
                    mac_address=gateway.mac,
                    conta=gateway.conta,
                    gateway=gateway,
                    forcar_renovacao=forcar_renovacao
                )
                messages.success(
                    request,
                    f'Certificado gerado com sucesso! Serial: {cert.serial_number[:20]}... '
                    f'Faça o download do pacote de provisionamento.'
                )
                return redirect('tds_new:admin_download_certificado', certificado_id=cert.pk)

            except CANaoConfiguradaError as e:
                messages.error(request, f'CA não configurada: {e}')
            except CertificadoJaExistenteError as e:
                messages.warning(request, str(e))
            except CertificadoServiceError as e:
                messages.error(request, f'Erro ao gerar certificado: {e}')
    else:
        form = GerarCertificadoFactoryForm(gateway=gateway)

    context = {
        'gateway': gateway,
        'cert_ativo': cert_ativo,
        'form': form,
        'titulo_pagina': f'Gerar Certificado — {gateway.device_id or gateway.mac}',
    }
    return render(request, 'admin_sistema/provisionamento/gerar_certificado.html', context)


# =============================================================================
# DOWNLOAD DO PACOTE DE PROVISIONAMENTO
# =============================================================================

@staff_member_required
def download_certificado_zip_view(request, certificado_id):
    """
    Download do pacote ZIP de provisionamento.

    Conteúdo do ZIP:
      - ca.crt       → Certificado raiz da CA
      - client.crt   → Certificado assinado do dispositivo
      - client.key   → Chave privada RSA (somente modo factory)
      - README_nvs.txt → Instruções de gravação NVS para ESP-IDF

    GET: Exibe página de confirmação com informações do certificado
    POST: Dispara o download do ZIP
    """
    from tds_new.services.certificados import CertificadoService, CANaoConfiguradaError

    certificado = get_object_or_404(CertificadoDevice, pk=certificado_id)

    if request.method == 'POST':
        try:
            service = CertificadoService()
            zip_bytes = service.gerar_zip_provisionamento(certificado)

            device_label = (certificado.device_id or certificado.mac_address).replace(':', '-')
            filename = f'provisioning_{device_label}_{certificado.serial_number[:12]}.zip'

            response = HttpResponse(zip_bytes, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except CANaoConfiguradaError as e:
            messages.error(request, f'CA não configurada: {e}')
        except Exception as e:
            messages.error(request, f'Erro ao gerar ZIP: {e}')

    context = {
        'certificado': certificado,
        'gateway': certificado.gateway,
        'titulo_pagina': f'Download — Pacote de Provisionamento',
    }
    return render(request, 'admin_sistema/provisionamento/download_certificado.html', context)


# =============================================================================
# REVOGAÇÃO DE CERTIFICADOS
# =============================================================================

@staff_member_required
def revogar_certificado_view(request, certificado_id):
    """
    Revogação de certificado X.509.

    GET: Exibe formulário de confirmação com motivo e notas
    POST: Executa revogação via CertificadoService.revogar_certificado()

    Após revogação, o serial do certificado deve ser incluído na CRL
    (Certificate Revocation List) do broker MQTT Mosquitto.
    """
    from tds_new.services.certificados import CertificadoService, CertificadoServiceError

    certificado = get_object_or_404(CertificadoDevice, pk=certificado_id)

    if certificado.is_revoked:
        messages.warning(request, f'Este certificado já foi revogado em {certificado.revoked_at}.')
        return redirect('tds_new:admin_certificados_list')

    if request.method == 'POST':
        form = RevogarCertificadoForm(request.POST)
        if form.is_valid():
            try:
                service = CertificadoService()
                service.revogar_certificado(
                    certificado=certificado,
                    motivo=form.cleaned_data['motivo'],
                    notas=form.cleaned_data.get('notas', ''),
                    usuario=request.user
                )
                messages.success(
                    request,
                    f'Certificado revogado com sucesso. '
                    f'Lembre-se de atualizar a CRL no broker MQTT.'
                )
                return redirect('tds_new:admin_certificados_list')

            except CertificadoServiceError as e:
                messages.error(request, str(e))
    else:
        form = RevogarCertificadoForm()

    context = {
        'certificado': certificado,
        'gateway': certificado.gateway,
        'form': form,
        'titulo_pagina': f'Revogar Certificado — {certificado.device_id or certificado.mac_address}',
    }
    return render(request, 'admin_sistema/provisionamento/revogar_certificado.html', context)


# =============================================================================
# BOOTSTRAP CERTIFICATES
# =============================================================================

@staff_member_required
def bootstrap_cert_list_view(request):
    """
    Lista todos os Bootstrap Certificates (ativo, inativos, revogados).

    O bootstrap cert é o cert compartilhado gravado na fábrica em todos os
    devices. Permite ao device o primeiro contato com o broker.
    """
    bootstrap_certs = BootstrapCertificate.objects.order_by('-created_at')
    ativo = BootstrapCertificate.objects.filter(is_active=True, is_revoked=False).first()

    context = {
        'bootstrap_certs': bootstrap_certs,
        'bootstrap_ativo': ativo,
        'titulo_pagina': 'Bootstrap Certificates — Fábrica',
    }
    return render(request, 'admin_sistema/provisionamento/bootstrap_list.html', context)


@staff_member_required
def gerar_bootstrap_cert_view(request):
    """
    Gera um novo Bootstrap Certificate para a fábrica.

    POST: CertificadoService.gerar_bootstrap_cert() → desativa anterior → download ZIP.
    O ZIP contém: bootstrap.crt + bootstrap.key + ca.crt + README_nvs.txt
    """
    from tds_new.services.certificados import CertificadoService, CANaoConfiguradaError, CertificadoServiceError

    bootstrap_ativo = BootstrapCertificate.objects.filter(is_active=True, is_revoked=False).first()

    if request.method == 'POST':
        form = GerarBootstrapCertForm(request.POST)
        if form.is_valid():
            try:
                service = CertificadoService()
                bootstrap = service.gerar_bootstrap_cert(
                    label=form.cleaned_data['label'],
                    criado_por=request.user,
                )
                messages.success(
                    request,
                    f'Bootstrap Certificate "{bootstrap.label}" gerado. '
                    f'Faça o download do pacote para gravação na fábrica.'
                )
                return redirect('tds_new:admin_download_bootstrap', bootstrap_id=bootstrap.pk)

            except CANaoConfiguradaError as e:
                messages.error(request, f'CA não configurada: {e}')
            except CertificadoServiceError as e:
                messages.error(request, f'Erro ao gerar bootstrap cert: {e}')
    else:
        form = GerarBootstrapCertForm()

    context = {
        'form': form,
        'bootstrap_ativo': bootstrap_ativo,
        'titulo_pagina': 'Gerar Bootstrap Certificate',
    }
    return render(request, 'admin_sistema/provisionamento/gerar_bootstrap.html', context)


@staff_member_required
def download_bootstrap_zip_view(request, bootstrap_id):
    """
    Download do pacote ZIP do Bootstrap Certificate para a fábrica.

    Conteúdo:
      bootstrap.crt  → Cert compartilhado (gravado em TODOS devices do lote)
      bootstrap.key  → Chave privada bootstrap
      ca.crt         → Certificado raiz da CA
      README_nvs.txt → Instruções de gravação NVS

    GET: Exibe página de confirmação.
    POST: Dispara download do ZIP.
    """
    from tds_new.services.certificados import CertificadoService, CANaoConfiguradaError

    bootstrap = get_object_or_404(BootstrapCertificate, pk=bootstrap_id)

    if request.method == 'POST':
        try:
            service = CertificadoService()
            zip_bytes = service.gerar_zip_bootstrap(bootstrap)
            filename = f'bootstrap_{bootstrap.label.replace(" ", "_")}_{bootstrap.serial_number[:12]}.zip'
            response = HttpResponse(zip_bytes, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except CANaoConfiguradaError as e:
            messages.error(request, f'CA não configurada: {e}')
        except Exception as e:
            messages.error(request, f'Erro ao gerar ZIP: {e}')

    context = {
        'bootstrap': bootstrap,
        'titulo_pagina': f'Download — Bootstrap "{bootstrap.label}"',
    }
    return render(request, 'admin_sistema/provisionamento/download_bootstrap.html', context)


@staff_member_required
def revogar_bootstrap_cert_view(request, bootstrap_id):
    """
    Revogação de emergência de Bootstrap Certificate.

    ⚠️ IMPACTA TODOS os devices ainda não provisionados que usam este cert.
    Use apenas em caso de comprometimento da chave privada.
    """
    from tds_new.services.certificados import CertificadoService, CertificadoServiceError

    bootstrap = get_object_or_404(BootstrapCertificate, pk=bootstrap_id)

    if bootstrap.is_revoked:
        messages.warning(request, f'Este bootstrap cert já foi revogado em {bootstrap.revoked_at}.')
        return redirect('tds_new:admin_bootstrap_list')

    if request.method == 'POST':
        form = RevogarBootstrapCertForm(request.POST)
        if form.is_valid():
            try:
                service = CertificadoService()
                service.revogar_bootstrap_cert(
                    bootstrap=bootstrap,
                    motivo=form.cleaned_data['motivo'],
                    notas=form.cleaned_data.get('notas', ''),
                    usuario=request.user,
                )
                messages.warning(
                    request,
                    f'⚠️ Bootstrap cert "{bootstrap.label}" REVOGADO. '
                    f'Atualize a CRL no broker MQTT imediatamente.'
                )
                return redirect('tds_new:admin_bootstrap_list')
            except CertificadoServiceError as e:
                messages.error(request, str(e))
    else:
        form = RevogarBootstrapCertForm()

    context = {
        'bootstrap': bootstrap,
        'form': form,
        'titulo_pagina': f'Revogar Bootstrap — "{bootstrap.label}"',
    }
    return render(request, 'admin_sistema/provisionamento/revogar_bootstrap.html', context)


# =============================================================================
# REGISTROS PENDENTES DE PROVISIONAMENTO
# =============================================================================

@staff_member_required
def registros_pendentes_view(request):
    """
    Lista os registros de auto-registro enviados pelos devices no primeiro boot.

    Devices que saíram da fábrica com o bootstrap cert e fizeram o primeiro
    contato aparecem aqui como PENDENTES. O admin aloca cada um para uma conta
    e emite o certificado individual.
    """
    status_filtro = request.GET.get('status', 'PENDENTE')
    registros = RegistroProvisionamento.objects.select_related(
        'gateway', 'certificado', 'processado_por', 'bootstrap_cert'
    ).order_by('-created_at')

    if status_filtro and status_filtro != 'todos':
        registros = registros.filter(status=status_filtro)

    context = {
        'registros': registros,
        'status_filtro': status_filtro,
        'total_pendente': RegistroProvisionamento.objects.filter(status='PENDENTE').count(),
        'total_provisionado': RegistroProvisionamento.objects.filter(status='PROVISIONADO').count(),
        'total_rejeitado': RegistroProvisionamento.objects.filter(status='REJEITADO').count(),
        'titulo_pagina': 'Registros de Provisionamento — Auto-Registro',
    }
    return render(request, 'admin_sistema/provisionamento/registros_pendentes.html', context)


@staff_member_required
def processar_registro_view(request, registro_id):
    """
    Admin aloca um device pendente para uma conta e (opcionalmente) emite cert individual.

    Fluxo:
      1. Admin seleciona conta destino + device_id + nome do gateway
      2. Gateway é criado na conta destino
      3. Se "gerar_certificado" marcado: CertificadoService.gerar_certificado_factory() é chamado
      4. RegistroProvisionamento atualizado → status=PROVISIONADO (ou ALOCADO)
      5. Admin pode fazer download do cert ZIP na etapa seguinte
    """
    from tds_new.services.certificados import CertificadoService, CertificadoServiceError, CANaoConfiguradaError

    registro = get_object_or_404(RegistroProvisionamento, pk=registro_id)

    if registro.status == 'PROVISIONADO':
        messages.info(request, 'Este device já foi provisionado.')
        return redirect('tds_new:admin_registros_pendentes')

    if registro.status == 'REJEITADO':
        messages.warning(request, 'Este registro foi rejeitado.')
        return redirect('tds_new:admin_registros_pendentes')

    if request.method == 'POST':
        form = ProcessarRegistroForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    conta = form.cleaned_data['conta']
                    device_id = form.cleaned_data['device_id']
                    nome_gateway = form.cleaned_data['nome_gateway']
                    gerar_cert = form.cleaned_data.get('gerar_certificado', True)
                    notas = form.cleaned_data.get('notas', '')

                    # Criar Gateway na conta destino
                    gateway = Gateway(
                        conta=conta,
                        mac=registro.mac_address,
                        device_id=device_id,
                        codigo=device_id,
                        nome=nome_gateway,
                        modelo=registro.modelo or '',
                        hardware_version=registro.fw_version or '',
                    )
                    gateway.save()

                    # Atualizar registro
                    registro.gateway = gateway
                    registro.processado_por = request.user
                    registro.processado_em = timezone.now()
                    registro.notas_admin = notas

                    cert = None
                    if gerar_cert:
                        service = CertificadoService()
                        cert = service.gerar_certificado_factory(
                            device_id=device_id,
                            mac_address=registro.mac_address,
                            conta=conta,
                            gateway=gateway,
                        )
                        registro.certificado = cert
                        registro.status = 'PROVISIONADO'
                        messages.success(
                            request,
                            f'✅ Device {registro.mac_address} alocado para "{conta.name}" '
                            f'e certificado gerado. Faça o download do pacote.'
                        )
                    else:
                        registro.status = 'ALOCADO'
                        messages.success(
                            request,
                            f'✅ Device {registro.mac_address} alocado para "{conta.name}". '
                            f'Gere o certificado quando estiver pronto.'
                        )

                    registro.save()

                    if cert:
                        return redirect('tds_new:admin_download_certificado', certificado_id=cert.pk)
                    return redirect('tds_new:admin_registros_pendentes')

            except CANaoConfiguradaError as e:
                messages.error(request, f'CA não configurada: {e}')
            except CertificadoServiceError as e:
                messages.error(request, f'Erro ao gerar certificado: {e}')
            except Exception as e:
                messages.error(request, f'Erro: {e}')
    else:
        form = ProcessarRegistroForm(initial={
            'nome_gateway': f'{registro.modelo or "Gateway"} — {registro.mac_address}',
        })

    context = {
        'registro': registro,
        'form': form,
        'titulo_pagina': f'Processar Registro — {registro.mac_address}',
    }
    return render(request, 'admin_sistema/provisionamento/processar_registro.html', context)


@staff_member_required
def rejeitar_registro_view(request, registro_id):
    """
    Rejeita um registro pendente (device não autorizado).
    POST apenas, com notas opcionais.
    """
    registro = get_object_or_404(RegistroProvisionamento, pk=registro_id)

    if request.method == 'POST':
        notas = request.POST.get('notas', '')
        registro.status = 'REJEITADO'
        registro.notas_admin = notas
        registro.processado_por = request.user
        registro.processado_em = timezone.now()
        registro.save()
        messages.warning(request, f'Registro {registro.mac_address} rejeitado.')

    return redirect('tds_new:admin_registros_pendentes')
