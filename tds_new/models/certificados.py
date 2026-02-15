"""
Modelos de Certificados X.509 - TDS New

CertificadoDevice: Gestão de certificados mTLS dos dispositivos IoT
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import re

from .base import SaaSBaseModel


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
    
    # Identificação do dispositivo
    mac_address = models.CharField(
        max_length=17,
        verbose_name="MAC Address",
        help_text="MAC address do dispositivo (formato aa:bb:cc:dd:ee:ff)"
    )
    
    # Certificado
    certificate_pem = models.TextField(
        verbose_name="Certificado PEM",
        help_text="Certificado X.509 no formato PEM (-----BEGIN CERTIFICATE-----)"
    )
    
    private_key_pem = models.TextField(
        blank=True,
        null=True,
        verbose_name="Chave Privada PEM",
        help_text="Chave privada RSA no formato PEM (armazenamento opcional - use com cuidado!)"
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
        unique_together = [
            ('conta', 'mac_address')
        ]
        indexes = [
            models.Index(fields=['conta', 'mac_address']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['mac_address', 'is_revoked']),
            models.Index(fields=['expires_at']),  # Query de renovação
            models.Index(fields=['is_revoked']),  # Query para CRL
            models.Index(fields=['renewal_scheduled', 'renewal_date']),  # OTA tasks
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        status = "REVOGADO" if self.is_revoked else "ATIVO"
        return f"{self.mac_address} - Serial {self.serial_number} - {status}"
    
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
        
        # TODO (Week 12): Atualizar CRL do Mosquitto broker
        # from tds_new.utils.crl import atualizar_crl_broker
        # atualizar_crl_broker()
        
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
