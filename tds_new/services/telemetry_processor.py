# ==============================================================================
# TDS New - Telemetry Processor Service
# ==============================================================================
# Arquivo: tds_new/services/telemetry_processor.py
# Responsabilidade: Lógica de negócio para processamento de telemetria IoT
# ==============================================================================

from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.utils import timezone
from tds_new.models import Gateway, Dispositivo, LeituraDispositivo
import logging

logger = logging.getLogger('telemetry_service')

# ==============================================================================
# SERVIÇO DE PROCESSAMENTO DE TELEMETRIA
# ==============================================================================

class TelemetryProcessorService:
    """
    Serviço de negócio para processamento de telemetria IoT
    
    Responsabilidades:
    - Validar schema JSON do payload
    - Lookup de dispositivos por código
    - Converter valores para Decimal (precisão financeira)
    - Bulk insert em LeituraDispositivo (performance)
    - Atualizar estado do gateway (last_seen, is_online)
    - Registrar auditoria de processamento
    
    Schema esperado do payload:
    {
        "gateway_mac": "aa:bb:cc:dd:ee:ff",
        "timestamp": "2026-02-18T14:30:00Z",
        "leituras": [
            {
                "dispositivo_codigo": "D01",
                "valor": 123.45,
                "unidade": "kWh"
            },
            ...
        ]
    }
    """
    
    def __init__(self, conta_id, gateway):
        """
        Inicializa o serviço
        
        Args:
            conta_id (int): ID da conta (multi-tenant)
            gateway (Gateway): Instância do gateway que enviou telemetria
        """
        self.conta_id = conta_id
        self.gateway = gateway
    
    def processar_telemetria(self, payload):
        """
        Processa payload JSON de telemetria e persiste no banco
        
        Args:
            payload (dict): Payload JSON da mensagem MQTT
        
        Returns:
            dict: Resultado do processamento
                {
                    'sucesso': True,
                    'leituras_criadas': int,
                    'timestamp': datetime
                }
        
        Raises:
            ValueError: Se payload é inválido
            Exception: Se ocorrer erro na persistência
        """
        # Validar schema básico
        if not self._validar_schema(payload):
            raise ValueError("Payload JSON não atende ao schema esperado")
        
        # Extrair timestamp
        try:
            timestamp = self._parse_timestamp(payload['timestamp'])
        except Exception as e:
            raise ValueError(f"Timestamp inválido: {e}")
        
        # Preparar objetos LeituraDispositivo para bulk_create
        leituras_data = payload.get('leituras', [])
        leituras_objetos = []
        leituras_ignoradas = 0
        
        for item in leituras_data:
            # Lookup de Dispositivo (validar que pertence ao gateway)
            try:
                dispositivo = self._buscar_dispositivo(item['dispositivo_codigo'])
            except Dispositivo.DoesNotExist:
                logger.warning(
                    f"⚠️ Dispositivo não encontrado: {item['dispositivo_codigo']} "
                    f"(gateway={self.gateway.codigo})"
                )
                leituras_ignoradas += 1
                continue
            except Exception as e:
                logger.error(f"❌ Erro ao buscar dispositivo: {e}")
                leituras_ignoradas += 1
                continue
            
            # Converter valor para Decimal (precisão financeira)
            try:
                valor = Decimal(str(item['valor']))
            except (InvalidOperation, ValueError) as e:
                logger.warning(
                    f"⚠️ Valor inválido ignorado: {item['valor']} "
                    f"(dispositivo={item['dispositivo_codigo']})"
                )
                leituras_ignoradas += 1
                continue
            
            # Validar valor positivo
            if valor < 0:
                logger.warning(
                    f"⚠️ Valor negativo ignorado: {valor} "
                    f"(dispositivo={item['dispositivo_codigo']})"
                )
                leituras_ignoradas += 1
                continue
            
            # Criar objeto LeituraDispositivo (ainda não salvo no banco)
            leitura = LeituraDispositivo(
                time=timestamp,
                conta_id=self.conta_id,
                gateway=self.gateway,
                dispositivo=dispositivo,
                valor=valor,
                unidade=item.get('unidade', 'unit'),
                payload_raw=item  # Guardar JSON original para auditoria
            )
            leituras_objetos.append(leitura)
        
        # Validar se há leituras válidas para processar
        if not leituras_objetos:
            logger.warning(
                f"⚠️ Nenhuma leitura válida encontrada no payload "
                f"(gateway={self.gateway.codigo}, total={len(leituras_data)}, ignoradas={leituras_ignoradas})"
            )
            return {
                'sucesso': False,
                'leituras_criadas': 0,
                'leituras_ignoradas': leituras_ignoradas,
                'timestamp': timestamp
            }
        
        # Transação atômica: bulk_create + update Gateway
        try:
            with transaction.atomic():
                # Bulk insert em hypertable TimescaleDB (performance)
                LeituraDispositivo.objects.bulk_create(leituras_objetos)
                
                # Atualizar estado do gateway
                self.gateway.last_seen = timezone.now()
                self.gateway.is_online = True
                self.gateway.save(update_fields=['last_seen', 'is_online'])
            
            logger.info(
                f"✅ Persistência concluída: {len(leituras_objetos)} leituras criadas "
                f"(gateway={self.gateway.codigo}, ignoradas={leituras_ignoradas})"
            )
            
            return {
                'sucesso': True,
                'leituras_criadas': len(leituras_objetos),
                'leituras_ignoradas': leituras_ignoradas,
                'timestamp': timestamp
            }
        
        except Exception as e:
            logger.exception(
                f"💥 Erro na persistência: {e} "
                f"(gateway={self.gateway.codigo})"
            )
            raise
    
    # ==========================================================================
    # MÉTODOS PRIVADOS (HELPERS)
    # ==========================================================================
    
    def _validar_schema(self, payload):
        """
        Valida schema básico do payload JSON
        
        Args:
            payload (dict): Payload a validar
        
        Returns:
            bool: True se válido, False caso contrário
        """
        # Campos obrigatórios no root
        campos_obrigatorios = ['gateway_mac', 'timestamp', 'leituras']
        
        for campo in campos_obrigatorios:
            if campo not in payload:
                logger.error(f"❌ Campo obrigatório ausente: '{campo}'")
                return False
        
        # Validar que 'leituras' é uma lista
        if not isinstance(payload['leituras'], list):
            logger.error(f"❌ Campo 'leituras' deve ser array (recebido: {type(payload['leituras']).__name__})")
            return False
        
        # Validar que 'leituras' não está vazio
        if len(payload['leituras']) == 0:
            logger.error("❌ Campo 'leituras' está vazio")
            return False
        
        # Validar schema de cada item de leitura
        for idx, item in enumerate(payload['leituras']):
            campos_item = ['dispositivo_codigo', 'valor', 'unidade']
            
            for campo in campos_item:
                if campo not in item:
                    logger.error(
                        f"❌ Campo obrigatório ausente em leituras[{idx}]: '{campo}' "
                        f"(item: {item})"
                    )
                    return False
        
        return True
    
    def _parse_timestamp(self, timestamp_str):
        """
        Converte timestamp ISO 8601 para datetime timezone-aware
        
        Args:
            timestamp_str (str): Timestamp em formato ISO 8601
                Exemplos válidos:
                - "2026-02-18T14:30:00Z"
                - "2026-02-18T14:30:00+00:00"
                - "2026-02-18T14:30:00-03:00"
        
        Returns:
            datetime: Datetime timezone-aware
        
        Raises:
            ValueError: Se timestamp é inválido
        """
        try:
            # Substituir 'Z' por '+00:00' (ISO 8601 compliant)
            timestamp_str = timestamp_str.replace('Z', '+00:00')
            
            # Parse com timezone
            dt = timezone.datetime.fromisoformat(timestamp_str)
            
            # Garantir que é timezone-aware
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            
            return dt
        
        except Exception as e:
            raise ValueError(f"Formato de timestamp inválido: {timestamp_str} ({e})")
    
    def _buscar_dispositivo(self, dispositivo_codigo):
        """
        Busca dispositivo por código, validando que pertence ao gateway
        
        Args:
            dispositivo_codigo (str): Código do dispositivo (ex: "D01")
        
        Returns:
            Dispositivo: Instância do dispositivo
        
        Raises:
            Dispositivo.DoesNotExist: Se dispositivo não existe ou não pertence ao gateway
        """
        try:
            dispositivo = Dispositivo.objects.get(
                gateway=self.gateway,
                codigo=dispositivo_codigo
            )
            return dispositivo
        
        except Dispositivo.DoesNotExist:
            # Re-raise com mensagem específica
            raise Dispositivo.DoesNotExist(
                f"Dispositivo '{dispositivo_codigo}' não encontrado para gateway "
                f"'{self.gateway.codigo}' (conta={self.gateway.conta.nome})"
            )
