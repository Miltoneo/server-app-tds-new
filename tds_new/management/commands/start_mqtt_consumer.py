# ==============================================================================
# TDS New - Django Management Command: start_mqtt_consumer
# ==============================================================================
# Arquivo: tds_new/management/commands/start_mqtt_consumer.py
# Responsabilidade: Comando Django para iniciar consumer MQTT de telemetria
# ==============================================================================

from django.core.management.base import BaseCommand, CommandError
from tds_new.consumers.mqtt_telemetry import create_mqtt_client
from tds_new.consumers.mqtt_config import MQTTConfig
import logging
import signal
import sys

logger = logging.getLogger('mqtt_consumer')

# ==============================================================================
# DJANGO MANAGEMENT COMMAND
# ==============================================================================

class Command(BaseCommand):
    help = 'Inicia o consumer MQTT para recebimento de telemetria IoT'
    
    def add_arguments(self, parser):
        """Adiciona argumentos CLI ao comando"""
        parser.add_argument(
            '--broker',
            type=str,
            default=None,
            help='Override do broker MQTT (padrão: settings.MQTT_BROKER_HOST)'
        )
        
        parser.add_argument(
            '--port',
            type=int,
            default=None,
            help='Override da porta MQTT (padrão: settings.MQTT_BROKER_PORT)'
        )
        
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Habilitar logs detalhados (DEBUG)'
        )
    
    def handle(self, *args, **options):
        """Executa o comando"""
        
        # Configurar nível de log se --debug
        if options['debug']:
            logging.getLogger('mqtt_consumer').setLevel(logging.DEBUG)
            logging.getLogger('telemetry_service').setLevel(logging.DEBUG)
            self.stdout.write(self.style.NOTICE("🐛 Modo DEBUG habilitado"))
        
        # Override de configurações via CLI (se fornecido)
        broker_host = options.get('broker') or MQTTConfig.BROKER_HOST
        broker_port = options.get('port') or (
            MQTTConfig.BROKER_PORT_TLS if MQTTConfig.USE_TLS else MQTTConfig.BROKER_PORT
        )
        
        # Mensagem de início
        self.stdout.write(self.style.SUCCESS("╔═══════════════════════════════════════════════════╗"))
        self.stdout.write(self.style.SUCCESS("║   TDS NEW - MQTT TELEMETRY CONSUMER              ║"))
        self.stdout.write(self.style.SUCCESS("╚═══════════════════════════════════════════════════╝"))
        self.stdout.write("")
        
        # Exibir configurações
        self.stdout.write(self.style.NOTICE("📋 Configurações:"))
        self.stdout.write(f"   • Broker: {broker_host}:{broker_port}")
        self.stdout.write(f"   • Client ID: {MQTTConfig.CLIENT_ID}")
        self.stdout.write(f"   • Topic: {MQTTConfig.TOPIC_TELEMETRY}")
        self.stdout.write(f"   • QoS: {MQTTConfig.QOS_SUBSCRIBE}")
        self.stdout.write(f"   • TLS: {'Habilitado ✅' if MQTTConfig.USE_TLS else 'Desabilitado ⚠️'}")
        self.stdout.write(f"   • Keepalive: {MQTTConfig.KEEPALIVE}s")
        self.stdout.write("")
        
        # Criar cliente MQTT
        try:
            self.stdout.write(self.style.NOTICE("🔧 Criando cliente MQTT..."))
            client = create_mqtt_client()
            self.stdout.write(self.style.SUCCESS("   ✅ Cliente criado"))
        except Exception as e:
            raise CommandError(f"Erro ao criar cliente MQTT: {e}")
        
        # Registrar handler para SIGINT/SIGTERM (graceful shutdown)
        def signal_handler(sig, frame):
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("👋 Sinal de interrupção recebido"))
            self.stdout.write(self.style.NOTICE("🛑 Desconectando do broker..."))
            client.disconnect()
            self.stdout.write(self.style.SUCCESS("✅ Consumer encerrado com sucesso"))
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Conectar ao broker
        try:
            self.stdout.write(self.style.NOTICE(f"🔗 Conectando ao broker {broker_host}:{broker_port}..."))
            client.connect(
                host=broker_host,
                port=broker_port,
                keepalive=MQTTConfig.KEEPALIVE
            )
            self.stdout.write(self.style.SUCCESS("   ✅ Conexão iniciada"))
        except Exception as e:
            raise CommandError(f"Erro ao conectar ao broker: {e}")
        
        # Iniciar loop infinito (blocking)
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("╔═══════════════════════════════════════════════════╗"))
        self.stdout.write(self.style.SUCCESS("║   CONSUMER ATIVO - Aguardando mensagens          ║"))
        self.stdout.write(self.style.SUCCESS("╚═══════════════════════════════════════════════════╝"))
        self.stdout.write(self.style.NOTICE("📡 Pressione Ctrl+C para encerrar"))
        self.stdout.write("")
        
        try:
            # Loop infinito (blocking) - processa mensagens MQTT
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("⚠️ Interrupção via teclado"))
        except Exception as e:
            raise CommandError(f"Erro no loop MQTT: {e}")
        finally:
            # Cleanup
            self.stdout.write(self.style.NOTICE("🧹 Limpeza final..."))
            client.disconnect()
            self.stdout.write(self.style.SUCCESS("✅ Desconectado do broker"))
