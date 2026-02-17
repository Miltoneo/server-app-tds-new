"""
Dashboard global administrativo
Week 8: Visão consolidada de todas as contas

Diferença da dashboard usuário final:
- Usuário final: vê apenas sua conta (filtrado por conta_ativa)
- Admin: vê TODAS as contas (sem filtro)
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from tds_new.models import Gateway, Dispositivo, Conta, CustomUser, CertificadoDevice


@staff_member_required
def dashboard_global(request):
    """
    Dashboard global do sistema com métricas consolidadas de todas as contas
    
    Requer:
    - is_staff=True ou is_superuser=True
    
    Métricas exibidas:
    - Total de contas ativas
    - Total de gateways (online/offline/nunca conectados)
    - Total de dispositivos (ativos/manutenção)
    - Total de certificados (válidos/expirados/revogados)
    - Top 5 contas com mais gateways
    - Atividade recente (últimos 7 dias)
    """
    # Estatísticas de Contas
    total_contas = Conta.objects.filter(is_active=True).count()
    contas_com_gateway = Conta.objects.filter(
        gateway__isnull=False
    ).distinct().count()
    
    # Estatísticas de Gateways
    total_gateways = Gateway.objects.count()
    gateways_online = Gateway.objects.filter(is_online=True).count()
    gateways_offline = Gateway.objects.filter(
        is_online=False,
        last_seen__isnull=False
    ).count()
    gateways_nunca_conectados = Gateway.objects.filter(last_seen__isnull=True).count()
    
    # Estatísticas de Dispositivos
    total_dispositivos = Dispositivo.objects.count()
    dispositivos_ativos = Dispositivo.objects.filter(status='ATIVO').count()
    dispositivos_manutencao = Dispositivo.objects.filter(status='MANUTENCAO').count()
    
    # Estatísticas de Certificados
    certificados_validos = CertificadoDevice.objects.filter(
        is_revoked=False,
        expires_at__gt=timezone.now()
    ).count()
    
    certificados_expirados = CertificadoDevice.objects.filter(
        expires_at__lt=timezone.now()
    ).count()
    
    certificados_revogados = CertificadoDevice.objects.filter(
        is_revoked=True
    ).count()
    
    # Certificados próximos da expiração (< 2 anos)
    data_limite = timezone.now() + timedelta(days=730)
    certificados_renova_breve = CertificadoDevice.objects.filter(
        is_revoked=False,
        expires_at__lt=data_limite,
        expires_at__gt=timezone.now()
    ).count()
    
    # Usuários
    total_usuarios = CustomUser.objects.filter(is_active=True).count()
    usuarios_admin = CustomUser.objects.filter(
        conta_memberships__role='admin'
    ).distinct().count()
    
    # Top 5 contas com mais gateways
    top_contas = Conta.objects.annotate(
        num_gateways=Count('gateway')
    ).filter(num_gateways__gt=0).order_by('-num_gateways')[:5]
    
    # Atividade recente (últimos 7 dias)
    data_7dias = timezone.now() - timedelta(days=7)
    gateways_recentes = Gateway.objects.filter(
        created_at__gte=data_7dias
    ).count()
    
    dispositivos_recentes = Dispositivo.objects.filter(
        created_at__gte=data_7dias
    ).count()
    
    context = {
        'titulo_pagina': 'Administração do Sistema TDS',
        
        # Métricas de Contas
        'total_contas': total_contas,
        'contas_com_gateway': contas_com_gateway,
        
        # Métricas de Gateways
        'total_gateways': total_gateways,
        'gateways_online': gateways_online,
        'gateways_offline': gateways_offline,
        'gateways_nunca_conectados': gateways_nunca_conectados,
        
        # Métricas de Dispositivos
        'total_dispositivos': total_dispositivos,
        'dispositivos_ativos': dispositivos_ativos,
        'dispositivos_manutencao': dispositivos_manutencao,
        
        # Métricas de Certificados
        'certificados_validos': certificados_validos,
        'certificados_expirados': certificados_expirados,
        'certificados_revogados': certificados_revogados,
        'certificados_renova_breve': certificados_renova_breve,
        
        # Métricas de Usuários
        'total_usuarios': total_usuarios,
        'usuarios_admin': usuarios_admin,
        
        # Atividade recente
        'gateways_recentes': gateways_recentes,
        'dispositivos_recentes': dispositivos_recentes,
        
        # Top 5
        'top_contas': top_contas,
    }
    
    return render(request, 'admin_sistema/dashboard.html', context)
