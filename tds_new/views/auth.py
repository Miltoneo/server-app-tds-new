"""
Views de Autenticação - TDS New
Sistema de login multi-tenant com seleção de conta.

Features:
- Login simples por email/senha
- Seleção de conta quando usuário tem múltiplas contas
- Validação de licença (conta ativa)
- Logout com limpeza de sessão

TODO (Week 8-9):
- Registro de usuários
- Ativação por email
- Reset de senha
- Integração com django-axes
- Integração com shared.assinaturas

Criado em: 14/02/2026
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model

from ..models import Conta, ContaMembership
from ..constants import Cenarios

User = get_user_model()
logger = logging.getLogger('tds_new.auth')


def _get_client_ip(request):
    """
    Extrai o IP real do cliente considerando proxies reversos.
    
    Args:
        request: HttpRequest object
        
    Returns:
        str: Endereço IP do cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_protect
def login_view(request):
    """
    View de login simples (Week 4-5)
    
    Fluxo:
    1. Autentica usuário por email/senha
    2. Se única conta: seleciona automaticamente e redireciona para dashboard
    3. Se múltiplas contas: redireciona para seleção de conta
    4. Se nenhuma conta: erro de acesso
    
    TODO (Week 8-9):
    - Adicionar django-axes (rate limiting)
    - Adicionar CAPTCHA após N tentativas
    - Auditoria de login
    """
    # Redireciona se já autenticado
    if request.user.is_authenticated:
        return redirect('tds_new:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        # Autentica usuário
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Usuário inativo. Entre em contato com o suporte.')
                logger.warning(f"Tentativa de login com usuário inativo: {email} | IP: {_get_client_ip(request)}")
                return render(request, 'auth/login.html')
            
            # Faz login
            auth_login(request, user)
            ip_origem = _get_client_ip(request)
            
            # Verifica contas do usuário
            memberships = ContaMembership.objects.filter(
                user=user,
                is_active=True
            ).select_related('conta')
            
            if memberships.count() == 0:
                # Nenhuma conta ativa
                auth_logout(request)
                messages.error(request, 'Usuário não possui acesso a nenhuma conta ativa.')
                logger.warning(f"Login sem conta: {email} | IP: {ip_origem}")
                return render(request, 'auth/login.html')
            
            elif memberships.count() == 1:
                # Uma única conta: seleciona automaticamente
                membership = memberships.first()
                conta = membership.conta
                
                # Valida se conta está ativa
                if not conta.is_active:
                    auth_logout(request)
                    messages.error(request, f'Conta {conta.name} está inativa.')
                    logger.warning(f"Login com conta inativa: {email} | Conta: {conta.name} | IP: {ip_origem}")
                    return redirect('tds_new:license_expired')
                
                # Define conta ativa na sessão
                request.session['conta_ativa_id'] = conta.id
                
                # Configura cenário home
                from .cenario import _configurar_cenario
                _configurar_cenario(request, Cenarios.HOME)
                
                messages.success(request, f'Bem-vindo(a) à {conta.name}!')
                logger.info(f"Login bem-sucedido: {email} | IP: {ip_origem} | Conta: {conta.name}")
                
                return redirect('tds_new:dashboard')
            
            else:
                # Múltiplas contas: precisa selecionar
                logger.info(f"Login bem-sucedido: {email} | IP: {ip_origem} | Múltiplas contas")
                return redirect('tds_new:select_account')
        
        else:
            # Falha de autenticação
            messages.error(request, 'Email ou senha incorretos.')
            logger.warning(f"Falha de login: {email} | IP: {_get_client_ip(request)}")
    
    return render(request, 'auth/login.html')


@login_required
def select_account_view(request):
    """
    View de seleção de conta (quando usuário tem múltiplas contas)
    
    Exibe lista de contas disponíveis para o usuário selecionar.
    """
    if request.method == 'POST':
        conta_id = request.POST.get('conta_id')
        
        try:
            # Verifica se usuário tem acesso à conta
            membership = ContaMembership.objects.get(
                user=request.user,
                conta_id=conta_id,
                is_active=True
            )
            conta = membership.conta
            
            # Valida se conta está ativa
            if not conta.is_active:
                messages.error(request, f'Conta {conta.name} está inativa.')
                return redirect('tds_new:license_expired')
            
            # Define conta ativa na sessão
            request.session['conta_ativa_id'] = conta.id
            
            # Configura cenário home
            from .cenario import _configurar_cenario
            _configurar_cenario(request, Cenarios.HOME)
            
            messages.success(request, f'Conta alterada para: {conta.name}')
            logger.info(f"Troca de conta: {request.user.email} | Conta: {conta.name}")
            
            return redirect('tds_new:dashboard')
        
        except ContaMembership.DoesNotExist:
            messages.error(request, 'Acesso negado a esta conta.')
            logger.warning(f"Tentativa de acesso negado: {request.user.email} | Conta ID: {conta_id}")
    
    # Lista contas disponíveis
    memberships = ContaMembership.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('conta')
    
    contas = [m.conta for m in memberships if m.conta.is_active]
    
    context = {
        'titulo_pagina': 'Selecionar Conta',
        'contas': contas,
    }
    
    return render(request, 'auth/select_account.html', context)


@login_required
def logout_view(request):
    """
    View de logout com limpeza de sessão
    """
    user_email = request.user.email
    auth_logout(request)
    
    # Limpa todas as variáveis de sessão relacionadas a conta
    request.session.flush()
    
    messages.success(request, 'Logout realizado com sucesso.')
    logger.info(f"Logout: {user_email} | IP: {_get_client_ip(request)}")
    
    return redirect('tds_new:login')


def license_expired_view(request):
    """
    View exibida quando conta tem licença expirada
    
    TODO (Week 8-9):
    - Integrar com shared.assinaturas para renovação
    - Exibir planos disponíveis
    - Botão para renovar via MercadoPago
    """
    context = {
        'titulo_pagina': 'Licença Expirada',
    }
    
    return render(request, 'auth/license_expired.html', context)
