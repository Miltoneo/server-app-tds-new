"""
Modelos de Certificados X.509 - TDS New

CertificadoDevice:         Certificado individual por dispositivo (emitido pelo backend)
BootstrapCertificate:      Certificado compartilhado gravado na fábrica em TODOS os devices
RegistroProvisionamento:   Pedido de auto-registro enviado pelo device no primeiro boot
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import re

from .base import SaaSBaseModel, BaseAuditMixin


class CertificadoDevice(SaaSBaseModel):
    """
    Certificados X.509 dos dispositivos IoT (10 anos de validade)
    
    Estratégia de Certificados:
    - Single Permanent Certificate (10 anos de validade)
    - Geração na fábrica (factory scripts)
    - Common Name = MAC address do dispositivo
    - Revogação via CRL (Certificate Revocation List)
    - Renovação via OTA 2 anos antes da expiração
    
    Características:
    - Algorithm: RSA 2048 bits
    - Validity: 10 anos (3650 dias)
    - Identificação: CN = MAC address (único por conta)
    - Serial Number: Único globalmente
    - CRL: Mosquitto broker configurado com CRL
    """
    
    REVOKE_REASON_CHOICES = [
        ('COMPROMISED', 'Comprometido/Roubado'),
        ('SUPERSEDED', 'Substituído por novo certificado'),
        ('CESSATION', 'Dispositivo descontinuado'),
        ('KEY_COMPROMISE', 'Chave privada comprometida'),
        ('AFFILIATION_CHANGED', 'Mudança de propriedade'),
        ('OTHER', 'Outro motivo'),
    ]
    
    # =========================================================================
    # IDENTIFICAÇÃO DO DISPOSITIVO
    # =========================================================================

    mac_address = models.CharField(
        max_length=17,
        verbose_name="MAC Address",
        help_text="MAC address do dispositivo (formato aa:bb:cc:dd:ee:ff)"
    )

    device_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Device ID",
        help_text="Identidade lógica MQTT do dispositivo (ex: AA0011). "
                  "Preenchido durante o provisionamento."
    )

    gateway = models.ForeignKey(
        'tds_new.Gateway',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificados',
        verbose_name="Gateway Associado",
        help_text="Gateway ao qual este certificado pertence (opcional — pode ser vinculado após alocação)"
    )

    # =========================================================================
    # CSR E CERTIFICADO (Modelo CSR — chave privada jamais sai do dispositivo)
    # =========================================================================

    csr_pem = models.TextField(
        blank=True,
        null=True,
        verbose_name="CSR PEM",
        help_text="Certificate Signing Request enviado pelo dispositivo. "
                  "Mantido para auditoria. O dispositivo gera o par de chaves internamente."
    )

    # Certificado
    certificate_pem = models.TextField(
        verbose_name="Certificado PEM",
        help_text="Certificado X.509 no formato PEM (-----BEGIN CERTIFICATE-----)"
    )

    # CAMPO LEGADO — NÃO UTILIZAR em novos fluxos.
    # No modelo CSR, a chave privada é gerada pelo dispositivo e nunca sai dele.
    private_key_pem = models.TextField(
        blank=True,
        null=True,
        verbose_name="Chave Privada PEM [LEGADO]",
        help_text="[LEGADO — NÃO USE] A chave privada é gerada pelo dispositivo e nunca deve ser "
                  "armazenada no servidor. Campo mantido apenas para compatibilidade histórica."
    )

    fingerprint_sha256 = models.CharField(
        max_length=95,
        blank=True,
        null=True,
        verbose_name="Fingerprint SHA-256",
        help_text="Hash SHA-256 do certificado (ex: AA:BB:CC:...). Calculado automaticamente."
    )
    
    # Metadados do certificado
    serial_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Serial Number",
        help_text="Número de série do certificado (único globalmente)"
    )
    
    expires_at = models.DateTimeField(
        verbose_name="Data de Expiração",
        help_text="Data/hora de expiração do certificado"
    )
    
    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Emissão",
        help_text="Data/hora de emissão do certificado"
    )
    
    # Revogação (CRL - Certificate Revocation List)
    is_revoked = models.BooleanField(
        default=False,
        verbose_name="Revogado",
        help_text="Indica se o certificado foi revogado (bloqueado no broker MQTT)"
    )
    
    revoked_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Revogação",
        help_text="Data/hora da revogação"
    )
    
    revoke_reason = models.CharField(
        max_length=30,
        choices=REVOKE_REASON_CHOICES,
        blank=True,
        null=True,
        verbose_name="Motivo da Revogação"
    )
    
    revoke_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações da Revogação",
        help_text="Detalhes adicionais sobre a revogação"
    )
    
    # OTA Renewal
    renewal_scheduled = models.BooleanField(
        default=False,
        verbose_name="Renovação Agendada",
        help_text="Indica se a renovação via OTA foi agendada"
    )
    
    renewal_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Renovação Agendada"
    )
    
    class Meta:
        verbose_name = "Certificado de Dispositivo"
        verbose_name_plural = "Certificados de Dispositivos"
        constraints = [
            # Apenas um certificado ATIVO por conta+MAC (certs revogados podem coexistir — histórico)
            models.UniqueConstraint(
                fields=['conta', 'mac_address'],
                condition=Q(is_revoked=False),
                name='unique_active_cert_per_device'
            ),
        ]
        indexes = [
            models.Index(fields=['conta', 'mac_address']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['mac_address', 'is_revoked']),
            models.Index(fields=['expires_at']),  # Query de renovação
            models.Index(fields=['is_revoked']),  # Query para CRL
            models.Index(fields=['renewal_scheduled', 'renewal_date']),  # OTA tasks
            models.Index(fields=['device_id'], name='tds_new_cer_device_id_idx'),
            models.Index(fields=['gateway'], name='tds_new_cer_gateway_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        status = "REVOGADO" if self.is_revoked else "ATIVO"
        label = self.device_id or self.mac_address
        return f"{label} - Serial {self.serial_number} - {status}"
    
    @property
    def dias_para_expiracao(self):
        """
        Dias restantes até a expiração
        
        Returns:
            int: Número de dias (negativo se já expirado)
        """
        if not self.expires_at:
            return 0
        
        delta = self.expires_at - timezone.now()
        return delta.days
    
    @property
    def precisa_renovacao(self):
        """
        Verifica se o certificado precisa de renovação (2 anos antes)
        
        Returns:
            bool: True se faltam <= 730 dias (2 anos)
        """
        return self.dias_para_expiracao <= 730
    
    @property
    def esta_expirado(self):
        """
        Verifica se o certificado está expirado
        
        Returns:
            bool: True se expirado
        """
        return timezone.now() > self.expires_at
    
    @property
    def status_certificado(self):
        """
        Status legível do certificado
        
        Returns:
            str: ATIVO | EXPIRADO | REVOGADO | RENOVACAO_PENDENTE
        """
        if self.is_revoked:
            return "REVOGADO"
        elif self.esta_expirado:
            return "EXPIRADO"
        elif self.precisa_renovacao:
            return "RENOVACAO_PENDENTE"
        else:
            return "ATIVO"
    
    @property
    def validade_restante_legivel(self):
        """
        Validade restante em formato legível
        
        Returns:
            str: Ex: "2 anos e 3 meses" ou "EXPIRADO"
        """
        dias = self.dias_para_expiracao
        
        if dias < 0:
            return "EXPIRADO"
        
        anos = dias // 365
        meses = (dias % 365) // 30
        dias_resto = (dias % 365) % 30
        
        partes = []
        if anos > 0:
            partes.append(f"{anos} ano{'s' if anos > 1 else ''}")
        if meses > 0:
            partes.append(f"{meses} {'meses' if meses > 1 else 'mês'}")
        if dias_resto > 0 and not partes:  # Só mostrar dias se < 1 mês total
            partes.append(f"{dias_resto} dia{'s' if dias_resto > 1 else ''}")
        
        return " e ".join(partes) if partes else "< 1 dia"
    
    def clean(self):
        """
        Validações customizadas do modelo
        """
        super().clean()
        
        # Validar formato do MAC address
        if self.mac_address:
            mac_pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
            if not re.match(mac_pattern, self.mac_address):
                raise ValidationError({
                    'mac_address': 'Formato inválido. Use o padrão aa:bb:cc:dd:ee:ff'
                })
            
            # Padronizar para lowercase
            self.mac_address = self.mac_address.lower()
        
        # Validar que certificado PEM está no formato correto
        if self.certificate_pem:
            if not self.certificate_pem.strip().startswith('-----BEGIN CERTIFICATE-----'):
                raise ValidationError({
                    'certificate_pem': 'Certificado deve estar no formato PEM (começar com -----BEGIN CERTIFICATE-----)'
                })
        
        # Validar que data de expiração está no futuro (para novos certificados)
        if not self.pk and self.expires_at:  # Apenas para novos registros
            if self.expires_at <= timezone.now():
                raise ValidationError({
                    'expires_at': 'Data de expiração deve estar no futuro'
                })
        
        # Validar campos de revogação
        if self.is_revoked:
            if not self.revoked_at:
                self.revoked_at = timezone.now()
            
            if not self.revoke_reason:
                raise ValidationError({
                    'revoke_reason': 'Motivo da revogação é obrigatório quando o certificado está revogado'
                })
    
    def save(self, *args, **kwargs):
        """Override save para executar validações"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def revogar(self, reason, notes=None, user=None):
        """
        Revoga o certificado (adiciona ao CRL)
        
        Args:
            reason (str): Motivo da revogação (choices)
            notes (str): Observações adicionais
            user (User): Usuário que revogou (para auditoria)
        
        Returns:
            bool: True se revogado com sucesso
        """
        if self.is_revoked:
            return False  # Já estava revogado
        
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.revoke_reason = reason
        self.revoke_notes = notes
        
        self.save(update_fields=['is_revoked', 'revoked_at', 'revoke_reason', 'revoke_notes', 'updated_at'])

        # Atualizar CRL do Mosquitto broker (fail-safe: erro não desfaz a revogação no banco)
        from tds_new.utils.crl import atualizar_crl_broker
        atualizar_crl_broker()

        return True
    
    def agendar_renovacao(self):
        """
        Agenda renovação via OTA (2 anos antes da expiração)
        
        Returns:
            bool: True se agendado com sucesso
        """
        if self.renewal_scheduled:
            return False  # Já agendado
        
        # Calcular data de início da renovação (2 anos antes)
        data_renovacao = self.expires_at - timedelta(days=730)
        
        # Se já passou do prazo, agendar para o próximo ciclo (amanhã)
        if data_renovacao < timezone.now():
            data_renovacao = timezone.now() + timedelta(days=1)
        
        self.renewal_scheduled = True
        self.renewal_date = data_renovacao
        
        self.save(update_fields=['renewal_scheduled', 'renewal_date', 'updated_at'])
        
        return True

# =============================================================================
# CERTIFICADO BOOTSTRAP (compartilhado — gravado na fábrica em todos os devices)
# =============================================================================

class BootstrapCertificate(BaseAuditMixin):
    """
    Certificado X.509 bootstrap — gravado na fábrica em TODOS os dispositivos.

    Propósito:
      Permite que o device se conecte ao broker na PRIMEIRA VEZ, mesmo sem estar
      registrado no sistema. O broker autoriza o bootstrap cert APENAS no tópico de
      provisionamento (tds_new/provision/request), bloqueando telemetria.

    Características:
      - GLOBAL — não pertence a nenhuma conta. Um único cert para toda a fábrica.
      - Apenas UM pode estar ativo por vez (is_active=True).
      - Rotação de lote: gera novo → marca anterior como inativo (não revogado).
      - Revogação de emergência: quando a chave privada é comprometida.
        Revogar = TODOS os devices ainda não provisionados ficam sem acesso ao broker.

    Fluxo:
      Fábrica → download do ZIP (bootstrap.crt + bootstrap.key) → flash em todos os devices
      Primeiro boot → device usa bootstrap cert → conecta ao broker → envia RegistroProvisionamento
      Admin aloca device → emite CertificadoDevice individual → device passa a usar cert individual

    Armazenamento NVS no ESP32 (partição 'bootstrap'):
      Chave NVS           | Arquivo
      bootstrap_cert      | bootstrap.crt
      bootstrap_key       | bootstrap.key
      ca_cert             | ca.crt
    """

    REVOKE_REASON_CHOICES = [
        ('COMPROMISED', 'Chave privada comprometida/vazada'),
        ('ROTATION', 'Rotação planejada de certificado'),
        ('OTHER', 'Outro motivo'),
    ]

    label = models.CharField(
        max_length=100,
        verbose_name="Identificação",
        help_text="Nome/versão deste bootstrap cert (ex: 'Produção 2026', 'Lote Q1-2026')"
    )

    # Certificado e chave (ambos armazenados — fábrica precisa dos dois para gravar nos devices)
    certificate_pem = models.TextField(
        verbose_name="Certificado PEM",
        help_text="Certificado X.509 no formato PEM. Gravado em TODOS os devices de fábrica."
    )
    private_key_pem = models.TextField(
        verbose_name="Chave Privada PEM",
        help_text="Chave privada RSA. Gravada junto com o cert em todos os devices de fábrica."
    )

    # Metadados PKI
    serial_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Serial Number"
    )
    fingerprint_sha256 = models.CharField(
        max_length=95,
        blank=True,
        null=True,
        verbose_name="Fingerprint SHA-256"
    )
    expires_at = models.DateTimeField(verbose_name="Expira em")

    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Apenas um bootstrap cert pode estar ativo por vez. "
                  "O cert ativo é o que deve ser gravado nos devices que saem da fábrica agora."
    )
    is_revoked = models.BooleanField(
        default=False,
        verbose_name="Revogado",
        help_text="Se revogado, devices usando este bootstrap cert não conseguirão mais "
                  "se conectar ao broker (broker deve atualizar CRL)."
    )
    revoked_at = models.DateTimeField(blank=True, null=True, verbose_name="Revogado em")
    revoke_reason = models.CharField(
        max_length=30,
        choices=REVOKE_REASON_CHOICES,
        blank=True,
        null=True,
        verbose_name="Motivo da Revogação"
    )
    revoke_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações da Revogação"
    )

    class Meta:
        verbose_name = "Certificado Bootstrap"
        verbose_name_plural = "Certificados Bootstrap"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_revoked']),
            models.Index(fields=['serial_number']),
        ]

    def __str__(self):
        estado = "REVOGADO" if self.is_revoked else ("ATIVO" if self.is_active else "INATIVO")
        return f"{self.label} — {estado} (serial {self.serial_number[:16]}...)"

    @property
    def dias_para_expiracao(self):
        if not self.expires_at:
            return 0
        return (self.expires_at - timezone.now()).days

    def revogar(self, motivo: str, notas: str = '', usuario=None):
        """Revoga este bootstrap cert."""
        if self.is_revoked:
            raise ValidationError("Este certificado bootstrap já foi revogado.")
        self.is_revoked = True
        self.is_active = False
        self.revoked_at = timezone.now()
        self.revoke_reason = motivo
        self.revoke_notes = notas
        self.save(update_fields=[
            'is_revoked', 'is_active', 'revoked_at',
            'revoke_reason', 'revoke_notes', 'updated_at'
        ])

        # Atualizar CRL do Mosquitto broker (fail-safe: erro não desfaz a revogação no banco)
        from tds_new.utils.crl import atualizar_crl_broker
        atualizar_crl_broker()

        return True

    def desativar(self):
        """Marca como inativo (rotação para novo cert sem revogar)."""
        if not self.is_active:
            return False
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
        return True

    def limpar_chave_privada(self):
        """
        Remove a chave privada do banco após o download do ZIP para a fábrica.

        A chave privada bootstrap é necessária somente uma vez — para gravar nos
        devices. Após o download, mantê-la persistida é um risco desnecessário:
        se o banco vazar, um atacante teria acesso ao cert que autentica todos os
        devices ainda não provisionados.

        Após a limpeza:
          - gerar_zip_bootstrap() lançará CertificadoServiceError (não é possível re-download)
          - O cert continua válido para conexões mTLS (broker usa apenas o .crt)

        Returns:
            bool: True se a chave foi limpa, False se já estava vazia
        """
        if not self.private_key_pem:
            return False
        self.private_key_pem = ''
        self.save(update_fields=['private_key_pem', 'updated_at'])
        return True


# =============================================================================
# REGISTRO DE PROVISIONAMENTO (pedido de auto-registro no primeiro boot)
# =============================================================================

class RegistroProvisionamento(BaseAuditMixin):
    """
    Registro enviado pelo device no primeiro boot, usando o bootstrap cert.

    O device publica para tds_new/provision/request (ou chama POST /api/provision/register/)
    com seus dados de identidade. O backend registra aqui e notifica os admins.

    Fluxo:
      1. Device usa bootstrap cert → conecta ao broker
      2. Device POST /api/provision/register/ com MAC, serial, modelo, fw_version
      3. RegistroProvisionamento criado com status=PENDENTE
      4. Admin vê na lista "Registros Pendentes"
      5. Admin aloca Gateway para uma Conta → gera CertificadoDevice individual
      6. Admin faz download do ZIP → grava no device (ou envia via MQTT OTA)
      7. Status → PROVISIONADO

    Nota:
      Este modelo não tem campo 'conta' pois o device ainda não pertence a nenhuma
      conta no momento do auto-registro. A conta é atribuída pelo admin na etapa 5.
    """

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente — aguardando alocação pelo admin'),
        ('ALOCADO', 'Alocado — gateway criado, aguardando cert'),
        ('PROVISIONADO', 'Provisionado — cert individual emitido e gravado'),
        ('REJEITADO', 'Rejeitado — device não autorizado'),
    ]

    # Identidade enviada pelo device
    mac_address = models.CharField(
        max_length=17,
        verbose_name="MAC Address",
        help_text="MAC address do device (aa:bb:cc:dd:ee:ff)"
    )
    serial_number_device = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Serial do Hardware",
        help_text="Serial gravado no hardware (ex: DCU-8210-001234)"
    )
    modelo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Modelo",
        help_text="Modelo do device (ex: DCU-8210)"
    )
    fw_version = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Versão do Firmware"
    )
    ip_origem = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="IP de Origem",
        help_text="IP do device no momento do registro (informativo)"
    )

    # Rastreabilidade do bootstrap cert usado
    bootstrap_cert = models.ForeignKey(
        BootstrapCertificate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros',
        verbose_name="Bootstrap Cert Utilizado",
        help_text="Bootstrap cert que o device usou para fazer este pedido de registro"
    )

    # CSR do dispositivo (Modelo PKI correto — chave privada jamais sai do device)
    # Campo opcional: preenchido quando o firmware envia o CSR no auto-registro.
    # Quando presente, o admin pode usar gerar_certificado_de_csr() no lugar do factory.
    csr_pem = models.TextField(
        blank=True,
        null=True,
        verbose_name="CSR (PKCS#10)",
        help_text="Certificate Signing Request enviado pelo device no auto-registro. "
                  "Quando presente, o cert individual é gerado pelo fluxo CSR (chave privada "
                  "permanece no device). Requer firmware atualizado."
    )

    # Estado do fluxo
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        verbose_name="Status"
    )

    # Resultado — preenchido após alocação + provisionamento
    gateway = models.ForeignKey(
        'tds_new.Gateway',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros_provisionamento',
        verbose_name="Gateway Alocado"
    )
    certificado = models.OneToOneField(
        CertificadoDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registro_provisionamento',
        verbose_name="Certificado Individual Emitido"
    )
    processado_por = models.ForeignKey(
        'tds_new.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros_processados',
        verbose_name="Processado Por"
    )
    processado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Processado Em"
    )
    notas_admin = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas do Admin"
    )

    class Meta:
        verbose_name = "Registro de Provisionamento"
        verbose_name_plural = "Registros de Provisionamento"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mac_address']),
            models.Index(fields=['status']),
            models.Index(fields=['mac_address', 'status']),
        ]

    def __str__(self):
        return f"{self.mac_address} — {self.get_status_display()} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"