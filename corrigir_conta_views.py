"""
Script para substituir todas as ocorrências de session.get('conta') por conta_ativa
"""
import re
import os

def substituir_conta_em_arquivo(filepath):
    """
    Substitui self.request.session.get('conta') por self.request.conta_ativa
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Conta ocorrências antes
    pattern = r"self\.request\.session\.get\('conta'\)"
    antes = len(re.findall(pattern, content))
    
    if antes > 0:
        # Faz substituição
        content_novo = re.sub(pattern, "self.request.conta_ativa", content)
        
        # Salva arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content_novo)
        
        # Verifica quantas substituições foram feitas
        depois = len(re.findall(pattern, content_novo))
        substituidas = antes - depois
        
        print(f"✅ {filepath}: {substituidas} substituições (antes: {antes}, depois: {depois})")
        return substituidas
    else:
        print(f"⏭️ {filepath}: Nenhuma ocorrência encontrada")
        return 0

# Arquivos a corrigir
arquivos = [
    'tds_new/views/gateway.py',
    'tds_new/views/dispositivo.py',
]

total = 0
for arquivo in arquivos:
    if os.path.exists(arquivo):
        total += substituir_conta_em_arquivo(arquivo)
    else:
        print(f"❌ {arquivo}: Arquivo não encontrado")

print(f"\n🎯 Total de substituições: {total}")
