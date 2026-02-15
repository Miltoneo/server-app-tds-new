"""
Script para testar se o servidor Django está rodando
"""
import socket
import sys

def check_server(host='127.0.0.1', port=8000, timeout=2):
    """Verifica se o servidor está aceitando conexões na porta especificada"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"✅ Servidor Django está RODANDO em {host}:{port}")
            print(f"\n🌐 Acesse o sistema em: http://{host}:{port}/")
            print(f"🔐 Login: http://{host}:{port}/admin/")
            print(f"\n📋 Credenciais:")
            print(f"   Username: admin")
            print(f"   Password: Admin@2026")
            return True
        else:
            print(f"❌ Servidor NÃO está rodando em {host}:{port}")
            print(f"   Código de erro: {result}")
            return False
    except socket.error as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

if __name__ == "__main__":
    is_running = check_server()
    sys.exit(0 if is_running else 1)
