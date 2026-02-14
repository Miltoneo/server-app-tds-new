"""
Testa conexões com serviços Docker
"""
import sys

def test_postgresql():
    """Testa conexão com PostgreSQL + TimescaleDB"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="db_tds_new",
            user="tsdb_django_d4j7g9",
            password="DjangoTS2025TimeSeries",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        
        # Verificar PostgreSQL
        cursor.execute("SELECT version()")
        pg_version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL: {pg_version.split(',')[0]}")
        
        # Verificar TimescaleDB
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
        result = cursor.fetchone()
        if result:
            print(f"✅ TimescaleDB: {result[0]}")
        else:
            print("⚠️  TimescaleDB: extensão não instalada")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL: {e}")
        return False

def test_redis():
    """Testa conexão com Redis"""
    try:
        import redis
        r = redis.Redis(
            host='localhost', 
            port=6379, 
            password='StrongRedisPass2024!', 
            db=0
        )
        r.ping()
        info = r.info()
        print(f"✅ Redis: {info['redis_version']}")
        return True
    except Exception as e:
        print(f"❌ Redis: {e}")
        return False

def test_mqtt():
    """Testa conexão com MQTT Mosquitto"""
    try:
        import paho.mqtt.client as mqtt
        
        connected = False
        
        def on_connect(client, userdata, flags, rc):
            nonlocal connected
            if rc == 0:
                connected = True
                print(f"✅ MQTT: Conectado com sucesso")
            else:
                print(f"❌ MQTT: Falha na conexão (código: {rc})")
        
        client = mqtt.Client()
        client.on_connect = on_connect
        client.connect("localhost", 1883, 60)
        client.loop_start()
        
        import time
        time.sleep(2)  # Aguarda callback de conexão
        
        client.loop_stop()
        return connected
    except Exception as e:
        print(f"❌ MQTT: {e}")
        return False

def main():
    print("🔍 Testando conexões com serviços Docker...\n")
    
    results = {
        'PostgreSQL': test_postgresql(),
        'Redis': test_redis(),
        'MQTT': test_mqtt()
    }
    
    print("\n" + "="*50)
    total = len(results)
    success = sum(results.values())
    print(f"Resultado: {success}/{total} serviços conectados")
    
    if success == total:
        print("✅ Todos os serviços estão funcionando!")
        sys.exit(0)
    else:
        print("⚠️  Alguns serviços não estão disponíveis")
        print("\nPara iniciar os serviços, execute:")
        print("  docker compose -f docker-compose.dev.yml up -d")
        sys.exit(1)

if __name__ == '__main__':
    main()
