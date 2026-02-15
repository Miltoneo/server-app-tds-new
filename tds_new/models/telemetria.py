"""
Modelos de Telemetria - TDS New

LeituraDispositivo: TimescaleDB hypertable para leituras de telemetria
ConsumoMensal: Continuous aggregate para consumo mensal agregado
"""

from django.db import models
from decimal import Decimal

from .base import Conta
from .dispositivos import Gateway, Dispositivo


class LeituraDispositivo(models.Model):
    """
    Leituras de telemetria dos dispositivos IoT - TimescaleDB Hypertable
    
    Características:
    - Hypertable particionada por timestamp (chunks de 1 dia)
    - Managed=False (gerenciado pelo TimescaleDB)
    - Queries otimizadas com índices compostos
    - Isolamento multi-tenant via conta_id
    
    Importante:
    - Hypertable deve ser criada manualmente via SQL após migration
    - Usar bulk_create() para inserções em lote
    """
    
    # Partition key (TimescaleDB)
    time = models.DateTimeField(
        verbose_name="Timestamp",
        help_text="Data/hora da leitura (partition key do TimescaleDB)",
        db_index=True
    )
    
    # Isolamento multi-tenant
    conta = models.ForeignKey(
        Conta,
        on_delete=models.CASCADE,
        verbose_name="Conta",
        help_text="Conta proprietária (isolamento multi-tenant)"
    )
    
    # Relacionamentos
    gateway = models.ForeignKey(
        Gateway,
        on_delete=models.CASCADE,
        verbose_name="Gateway",
        help_text="Gateway que enviou a telemetria"
    )
    
    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.CASCADE,
        verbose_name="Dispositivo",
        help_text="Dispositivo que gerou a leitura"
    )
    
    # Dados da leitura
    valor = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="Valor",
        help_text="Valor da leitura"
    )
    
    unidade = models.CharField(
        max_length=10,
        verbose_name="Unidade",
        help_text="Unidade de medida (kWh, m³, L, °C, etc)"
    )
    
    # Payload completo (opcional - para debug/auditoria)
    payload_raw = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Payload Raw",
        help_text="Payload JSON completo recebido via MQTT (opcional)"
    )
    
    class Meta:
        managed = False  # Gerenciado pelo TimescaleDB
        db_table = 'tds_new_leitura_dispositivo'
        verbose_name = "Leitura de Dispositivo"
        verbose_name_plural = "Leituras de Dispositivos"
        indexes = [
            # Índices para queries típicas
            models.Index(fields=['conta', 'time']),
            models.Index(fields=['dispositivo', 'time']),
            models.Index(fields=['gateway', 'time']),
            models.Index(fields=['conta', 'dispositivo', 'time']),
        ]
        # Não definir ordering padrão (otimização para hypertable)
    
    def __str__(self):
        return f"{self.dispositivo.codigo} - {self.valor} {self.unidade} @ {self.time}"
    
    @staticmethod
    def criar_leituras_lote(leituras_data):
        """
        Cria leituras em lote (mais eficiente para TimescaleDB)
        
        Args:
            leituras_data (list): Lista de dicts com dados das leituras
        
        Returns:
            int: Número de leituras criadas
        
        Example:
            leituras = [
                {
                    'time': datetime.now(),
                    'conta': conta_obj,
                    'gateway': gateway_obj,
                    'dispositivo': dispositivo_obj,
                    'valor': Decimal('123.45'),
                    'unidade': 'kWh',
                    'payload_raw': {...}
                },
                ...
            ]
            LeituraDispositivo.criar_leituras_lote(leituras)
        """
        objetos = [LeituraDispositivo(**data) for data in leituras_data]
        return LeituraDispositivo.objects.bulk_create(objetos)


class ConsumoMensal(models.Model):
    """
    Consumo mensal agregado - TimescaleDB Continuous Aggregate
    
    Características:
    - View materializada atualizada automaticamente
    - Agregação mensal via time_bucket('1 month', time)
    - Políticas de refresh configuráveis
    - Managed=False (gerenciado pelo TimescaleDB)
    
    Importante:
    - View deve ser criada manualmente via SQL após migration
    - Dados são atualizados automaticamente pelo TimescaleDB
    """
    
    # Aggregation key
    mes_referencia = models.DateField(
        verbose_name="Mês de Referência",
        help_text="Primeiro dia do mês (resultado do time_bucket)"
    )
    
    # Isolamento multi-tenant
    conta = models.ForeignKey(
        Conta,
        on_delete=models.CASCADE,
        verbose_name="Conta"
    )
    
    # Relacionamento
    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.CASCADE,
        verbose_name="Dispositivo"
    )
    
    # Dados agregados
    total_consumo = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="Consumo Total",
        help_text="Soma de todas as leituras do mês"
    )
    
    media_diaria = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="Média Diária",
        help_text="Média das leituras do mês"
    )
    
    leituras_count = models.IntegerField(
        verbose_name="Quantidade de Leituras",
        help_text="Número de leituras no período"
    )
    
    class Meta:
        managed = False  # Gerenciado pelo TimescaleDB (continuous aggregate)
        db_table = 'tds_new_consumo_mensal'
        verbose_name = "Consumo Mensal"
        verbose_name_plural = "Consumos Mensais"
        # Indexes gerenciados pelo TimescaleDB automaticamente
    
    def __str__(self):
        return f"{self.dispositivo.codigo} - {self.mes_referencia.strftime('%m/%Y')} - {self.total_consumo}"
