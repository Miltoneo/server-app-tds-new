"""
Context Processors para TDS New
Injetam variáveis globais no contexto de todos os templates
"""
from django.conf import settings
from tds_new.models import ContaMembership, Conta
from tds_new.middleware import get_current_account


def conta_context(request):
    """
    DIRETRIZ OBRIGATÓRIA: Contexto de Conta Multi-tenant
    -----------------------------------------------------
    - Injeta 'conta' no contexto dos templates via context processor, nunca manualmente nas views.
    - O valor é obtido do middleware (request.conta_ativa) ou da sessão como fallback.
    - Nunca busque manualmente a conta ativa via query nas views.
    - Toda lógica de obtenção, validação e fallback da conta deve estar centralizada aqui.
    - Este padrão é obrigatório para garantir isolamento multi-tenant, consistência e evitar bugs recorrentes.
    """
    # Prioridade 1: Conta definida pelo middleware no request
    if hasattr(request, 'conta_ativa'):
        return {
            'conta': request.conta_ativa,
            'conta_id': request.conta_ativa.id,
        }
    
    # Prioridade 2: Conta na sessão (fallback)
    conta_id = request.session.get('conta_ativa_id')
    if conta_id:
        try:
            conta = Conta.objects.get(id=conta_id, is_active=True)
            return {
                'conta': conta,
                'conta_id': conta.id,
            }
        except Conta.DoesNotExist:
            pass
    
    # Nenhuma conta ativa
    return {
        'conta': None,
        'conta_id': None,
    }


def app_version(request):
    """
    Injeta a versão da aplicação no contexto dos templates
    """
    return {
        "APP_VERSION": settings.APP_VERSION
    }


def session_context(request):
    """
    Injeta variáveis de sessão no contexto dos templates
    - titulo_pagina: título da página atual
    - cenario_nome: nome do cenário ativo (Dashboard, Dispositivos, Telemetria, etc)
    - menu_nome: nome do menu ativo
    """
    return {
        'titulo_pagina': request.session.get('titulo_pagina', ''),
        'cenario_nome': request.session.get('cenario_nome', ''),
        'menu_nome': request.session.get('menu_nome', ''),
    }


def usuario_context(request):
    """
    DIRETRIZ OBRIGATÓRIA: Contexto de Permissões do Usuário
    --------------------------------------------------------
    - Injeta informações de permissão do usuário atual no contexto de todos os templates.
    - 'usuario_admin': indica se o usuário tem role='admin' na conta ativa atual.
    - 'usuario_pode_editar': indica se o usuário tem permissão de editor ou admin.
    - 'usuario_pode_visualizar': indica se o usuário tem qualquer acesso à conta.
    - Usado para controlar visibilidade de links/funcionalidades administrativas na UI.
    - Links sem permissão devem estar visíveis mas desabilitados (UX best practice).
    - Fonte: Implementado conforme estratégia de prj_medicos e Nielsen Norman Group Guidelines.
    """
    if not request.user.is_authenticated:
        return {
            'usuario_atual': None,
            'usuario_admin': False,
            'usuario_pode_editar': False,
            'usuario_pode_visualizar': False,
        }
    
    # Verifica se usuário é admin na conta ativa atual
    conta_id = request.session.get('conta_ativa_id')
    usuario_admin = False
    usuario_pode_editar = False
    usuario_pode_visualizar = False
    
    if conta_id:
        # Busca membership ativa na conta atual
        membership = ContaMembership.objects.filter(
            user=request.user,
            conta_id=conta_id,
            is_active=True
        ).first()
        
        if membership:
            usuario_admin = (request.user.is_superuser or membership.is_admin())
            usuario_pode_editar = (request.user.is_superuser or membership.can_edit())
            usuario_pode_visualizar = membership.can_view()
    else:
        # Fallback: verifica se é admin em qualquer conta ativa
        usuario_admin = (
            request.user.is_superuser or 
            ContaMembership.objects.filter(
                user=request.user,
                is_active=True,
                role=ContaMembership.ROLE_ADMIN
            ).exists()
        )
    
    return {
        'usuario_atual': request.user,
        'usuario_admin': usuario_admin,
        'usuario_pode_editar': usuario_pode_editar,
        'usuario_pode_visualizar': usuario_pode_visualizar,
    }
 
                ContaMembership.objects.filter(
                    user=request.user,
                    conta_id=conta_id,
                    is_active=True,
                    role='admin'
                ).exists()
            )
        else:
            # Fallback: verifica se é admin em qualquer conta ativa
            usuario_admin = (
                request.user.is_superuser or 
                ContaMembership.objects.filter(
                    user=request.user,
                    is_active=True,
                    role='admin'
                ).exists()
            )
        
        return {
            'usuario_atual': request.user,
            'usuario_admin': usuario_admin,
        }
    return {
        'usuario_atual': None,
        'usuario_admin': False,
    }
