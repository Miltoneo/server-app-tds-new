"""
Modelos de Dispositivos IoT - TDS New

Gateway: Agregador de dispositivos (publica via MQTT)
Dispositivo: Sensor/medidor conectado ao gateway
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import re

from .base import SaaSBaseModel


class Gateway(SaaSBaseModel):
    """
    Gateway de telemetria - Agrega dispositivos Modbus RTU e publica via MQTT
    
    Características:
    - MAC address único (identificação no broker MQTT)
    - Suporta até 8 dispositivos (configurável)
    - Publica telemetria via MQTT com mTLS
    - Localização geográfica (latitude/longitude)
    """
    
    # Identificação
    codigo = models.CharField(
        max_length=30,
        verbose_name="Código",
        help_text="Código único do gateway dentro da conta"
    )
    
    mac = models.CharField(
        max_length=17,
        verbose_name="MAC Address",
        help_text="Endereço MAC no formato aa:bb:cc:dd:ee:ff (usado como identificador MQTT)"
    )
    
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome"
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição"
    )
    
    # Localização
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Latitude",
        help_text="Coordenada geográfica"
    )
    
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Longitude",
        help_text="Coordenada geográfica"
    )
    
    # Capacidade
    qte_max_dispositivos = models.IntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(32)],
        verbose_name="Quantidade Máxima de Dispositivos",
        help_text="Capacidade máxima de dispositivos conectados (padrão: 8)"
    )
    
    # Status de Conexão
    is_online = models.BooleanField(
        default=False,
        verbose_name="Online",
        help_text="Indica se o gateway está conectado ao broker MQTT"
    )
    
    last_seen = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Última Comunicação",
        help_text="Data/hora da última telemetria recebida"
    )
    
    firmware_version = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Versão do Firmware",
        help_text="Versão do firmware instalado no gateway"
    )

    # =========================================================================
    # IDENTIDADE DE FÁBRICA (Factory Provisioning — NVS partition 'setup')
    # Preenchidos no momento do provisionamento/gravação do dispositivo.
    # =========================================================================

    device_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Device ID",
        help_text="Identidade lógica MQTT gravada na NVS de fábrica (ex: AA0011). "
                  "Usada como ClientID no broker e como base do gateway_code."
    )

    serial_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número de Série",
        help_text="Identidade física irrevogável gravada na NVS de fábrica (ex: AA0011). "
                  "Vinculada ao hardware — nunca muda mesmo se device_id mudar."
    )

    gateway_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Gateway Code",
        help_text="Código derivado em runtime pelo firmware: '{device_id}-{LAST4HEX_MAC}' "
                  "(ex: AA0011-E1F2). Preenchido pelo backend na primeira conexão MQTT."
    )

    modelo = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Modelo de Hardware",
        help_text="Modelo do hardware gravado na NVS de fábrica (ex: DCU-1800)"
    )

    hardware_version = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Versão de Hardware",
        help_text="Revisão de hardware gravada na NVS de fábrica (ex: 1.0)"
    )

    class Meta:
        verbose_name = "Gateway"
        verbose_name_plural = "Gateways"
        unique_together = [
            ('conta', 'codigo'),
            ('conta', 'mac')
        ]
        indexes = [
            models.Index(fields=['conta', 'is_online']),
            models.Index(fields=['conta', 'mac']),
            models.Index(fields=['conta', 'codigo']),
            models.Index(fields=['device_id'], name='tds_new_gw_device_id_idx'),
            models.Index(fields=['serial_number'], name='tds_new_gw_serial_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        if self.device_id:
            return f"{self.device_id} - {self.nome}"
        return f"{self.codigo} - {self.nome}"
    
    @property
    def status_conexao(self):
        """
        Retorna status de conexão legível
        
        Returns:
            str: ONLINE | OFFLINE | NUNCA_CONECTADO
        """
        if not self.last_seen:
            return "NUNCA_CONECTADO"
        elif self.is_online:
            return "ONLINE"
        else:
            return "OFFLINE"
    
    @property
    def dispositivos_count(self):
        """
        Contagem de dispositivos ativos vinculados ao gateway
        
        Returns:
            int: Número de dispositivos com status ATIVO
        """
        return self.dispositivo_set.filter(status='ATIVO').count()
    
    @property
    def capacidade_disponivel(self):
        """
        Slots disponíveis para novos dispositivos
        
        Returns:
            int: Número de slots disponíveis
        """
        return self.qte_max_dispositivos - self.dispositivos_count
    
    @property
    def percentual_uso(self):
        """
        Percentual de uso da capacidade
        
        Returns:
            float: Percentual entre 0 e 100
        """
        if self.qte_max_dispositivos == 0:
            return 0
        return (self.dispositivos_count / self.qte_max_dispositivos) * 100
    
    def clean(self):
        """
        Validações customizadas do modelo
        """
        super().clean()
        
        # Validar formato do MAC address
        if self.mac:
            mac_pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
            if not re.match(mac_pattern, self.mac):
                raise ValidationError({
                    'mac': 'Formato inválido. Use o padrão aa:bb:cc:dd:ee:ff (hexadecimal com dois dígitos separados por :)'
                })
            
            # Padronizar para lowercase
            self.mac = self.mac.lower()
            
            # Validar unicidade do MAC dentro da conta (se não for o mesmo objeto)
            if self.pk:
                qs = Gateway.objects.filter(conta=self.conta, mac=self.mac).exclude(pk=self.pk)
            else:
                qs = Gateway.objects.filter(conta=self.conta, mac=self.mac)
            
            if qs.exists():
                raise ValidationError({
                    'mac': f'Gateway com MAC address {self.mac} já existe nesta conta'
                })
    
    def save(self, *args, **kwargs):
        """Override save para executar validações"""
        self.full_clean()
        super().save(*args, **kwargs)


class Dispositivo(SaaSBaseModel):
    """
    Dispositivo IoT conectado ao gateway
    
    Tipos:
    - MEDIDOR: Medidor de consumo (água, energia, gás) via Modbus RTU
    - SENSOR: Sensor genérico (temperatura, umidade, pressão)
    - ATUADOR: Dispositivo de controle (válvula, relé)
    
    Protocolos:
    - Modbus RTU: Slave ID obrigatório (1-247), register obrigatório (1-65535)
    - WiFi/Ethernet direto: MAC address obrigatório (opcional para Modbus)
    """
    
    TIPO_CHOICES = [
        ('MEDIDOR', 'Medidor de Consumo'),
        ('SENSOR', 'Sensor'),
        ('ATUADOR', 'Atuador'),
    ]
    
    MODO_CHOICES = [
        ('AUTO', 'Automático'),
        ('MANUAL', 'Manual'),
    ]
    
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('INATIVO', 'Inativo'),
        ('MANUTENCAO', 'Manutenção'),
    ]
    
    # Relacionamento
    gateway = models.ForeignKey(
        Gateway,
        on_delete=models.CASCADE,
        verbose_name="Gateway",
        help_text="Gateway ao qual o dispositivo está conectado"
    )
    
    # Identificação
    codigo = models.CharField(
        max_length=20,
        verbose_name="Código",
        help_text="Código único do dispositivo dentro do gateway (ex: D01, D02)"
    )
    
    mac = models.CharField(
        max_length=17,
        blank=True,
        null=True,
        verbose_name="MAC Address",
        help_text="MAC address (obrigatório apenas para dispositivos WiFi/Ethernet direto)"
    )
    
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome"
    )
    
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição"
    )
    
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='MEDIDOR',
        verbose_name="Tipo"
    )
    
    # Configuração Modbus RTU (obrigatório para tipo=MEDIDOR)
    register_modbus = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        verbose_name="Registro Modbus",
        help_text="Registro Modbus a ser lido (1-65535)"
    )
    
    slave_id = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(247)],
        verbose_name="Slave ID",
        help_text="ID do dispositivo no barramento Modbus (1-247)"
    )
    
    # Operação
    modo = models.CharField(
        max_length=10,
        choices=MODO_CHOICES,
        default='AUTO',
        verbose_name="Modo de Operação"
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='ATIVO',
        verbose_name="Status"
    )
    
    # Alarmes
    val_alarme_dia = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Valor de Alarme Diário",
        help_text="Valor limite para disparo de alarme diário"
    )
    
    val_alarme_mes = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Valor de Alarme Mensal",
        help_text="Valor limite para disparo de alarme mensal"
    )
    
    # Status de Conexão
    is_online = models.BooleanField(
        default=False,
        verbose_name="Online",
        help_text="Indica se o dispositivo está respondendo"
    )
    
    last_seen = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Última Leitura",
        help_text="Data/hora da última leitura recebida"
    )
    
    firmware_version = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Versão do Firmware"
    )
    
    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"
        unique_together = [
            ('gateway', 'codigo')
        ]
        indexes = [
            models.Index(fields=['conta', 'gateway', 'status']),
            models.Index(fields=['conta', 'mac']),
            models.Index(fields=['gateway', 'codigo']),
        ]
        ordering = ['gateway', 'codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome} ({self.gateway.codigo})"
    
    @property
    def status_conexao(self):
        """
        Retorna status de conexão legível
        
        Returns:
            str: ONLINE | OFFLINE | NUNCA_LIDO
        """
        if not self.last_seen:
            return "NUNCA_LIDO"
        elif self.is_online:
            return "ONLINE"
        else:
            return "OFFLINE"
    
    @property
    def identificador_completo(self):
        """
        Identificador completo: Gateway/Dispositivo
        
        Returns:
            str: Ex: "GW001/D01"
        """
        return f"{self.gateway.codigo}/{self.codigo}"
    
    def clean(self):
        """
        Validações customizadas do modelo
        """
        super().clean()
        
        # Validar campos obrigatórios para tipo MEDIDOR (Modbus RTU)
        if self.tipo == 'MEDIDOR':
            if not self.slave_id:
                raise ValidationError({
                    'slave_id': 'Slave ID é obrigatório para dispositivos do tipo Medidor (Modbus RTU)'
                })
            
            if not (1 <= self.slave_id <= 247):
                raise ValidationError({
                    'slave_id': 'Slave ID deve estar entre 1 e 247'
                })
            
            if not self.register_modbus:
                raise ValidationError({
                    'register_modbus': 'Registro Modbus é obrigatório para dispositivos do tipo Medidor'
                })
            
            if not (1 <= self.register_modbus <= 65535):
                raise ValidationError({
                    'register_modbus': 'Registro Modbus deve estar entre 1 e 65535'
                })
        
        # Validar formato do MAC address (se informado)
        if self.mac:
            mac_pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
            if not re.match(mac_pattern, self.mac):
                raise ValidationError({
                    'mac': 'Formato inválido. Use o padrão aa:bb:cc:dd:ee:ff'
                })
            
            # Padronizar para lowercase
            self.mac = self.mac.lower()
            
            # Validar unicidade do MAC dentro da conta (se não for o mesmo objeto)
            if self.pk:
                qs = Dispositivo.objects.filter(conta=self.conta, mac=self.mac).exclude(pk=self.pk)
            else:
                qs = Dispositivo.objects.filter(conta=self.conta, mac=self.mac)
            
            if qs.exists():
                raise ValidationError({
                    'mac': f'Dispositivo com MAC address {self.mac} já existe nesta conta'
                })
        
        # Validar capacidade do gateway
        if self.gateway_id:
            # Contar dispositivos ativos no gateway (excluindo este se for edição)
            if self.pk:
                dispositivos_ativos = Dispositivo.objects.filter(
                    gateway=self.gateway,
                    status='ATIVO'
                ).exclude(pk=self.pk).count()
            else:
                dispositivos_ativos = Dispositivo.objects.filter(
                    gateway=self.gateway,
                    status='ATIVO'
                ).count()
            
            # Só validar se o dispositivo está sendo ativado
            if self.status == 'ATIVO' and dispositivos_ativos >= self.gateway.qte_max_dispositivos:
                raise ValidationError({
                    'gateway': f'Gateway {self.gateway.codigo} atingiu capacidade máxima '
                              f'({self.gateway.qte_max_dispositivos} dispositivos ativos). '
                              f'Desative um dispositivo existente ou aumente a capacidade do gateway.'
                })
    
    def save(self, *args, **kwargs):
        """Override save para executar validações"""
        self.full_clean()
        super().save(*args, **kwargs)
