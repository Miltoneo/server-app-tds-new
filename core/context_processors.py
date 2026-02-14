from django.conf import settings
from tds_new.models import ContaMembership, Conta, Empresa
from tds_new.middleware.tenant_middleware import get_current_account

def conta_context(request):
    """
    DIRETRIZ OBRIGATÓRIA: Contexto de Conta Multi-tenant
    -----------------------------------------------------
    - Injeta 'conta_id' no contexto dos templates via context processor, nunca manualmente nas views.
    - O valor de conta_id é obtido explicitamente da sessão (armazenado como 'conta_id').
    - Nunca busque manualmente a conta ativa em request.user ou via query nas views.
    - Toda lógica de obtenção, validação e fallback da conta deve estar centralizada aqui.
    - Se precisar de outra variável global (ex: empresa, tenant), crie um novo context processor.
    - Este padrão é obrigatório para garantir isolamento multi-tenant, consistência e evitar bugs recorrentes.
    """
    conta_id = request.session.get('conta_id')
    conta = None
    if conta_id:
        from tds_new.models import Conta
        try:
            conta = Conta.objects.get(id=conta_id)
        except Conta.DoesNotExist:
            conta = None
    return {'conta_id': conta_id, 'conta': conta}

def app_version(request):
    return {"APP_VERSION": settings.APP_VERSION}

def session_context(request):
    """
    Injeta variáveis de sessão no contexto dos templates
    - titulo_pagina: título da página atual
    - cenario_nome: nome do cenário ativo (Empresa, Financeiro, etc)
    - menu_nome: nome do menu ativo
    - empresa_nome: nome da empresa selecionada
    - mes_ano: mês/ano de competência ativo
    """
    return {
        'titulo_pagina': request.session.get('titulo_pagina', ''),
        'cenario_nome': request.session.get('cenario_nome', ''),
        'menu_nome': request.session.get('menu_nome', ''),
        'empresa_nome': request.session.get('empresa_nome', ''),
        'mes_ano': request.session.get('mes_ano', ''),
    }

def empresa_context(request):
    """
    DIRETRIZ OBRIGATÓRIA: Contexto de Empresa Multi-tenant
    -----------------------------------------------------
    - Sempre utilize a variável 'empresa' injetada por este context processor em views, forms e templates.
    - Nunca busque manualmente a empresa ativa em request.session ou via query nas views.
    - Toda lógica de obtenção, validação e fallback da empresa deve estar centralizada aqui.
    - Se a empresa não estiver disponível, este context processor já trata o erro e exibe mensagem apropriada.
    - Se precisar de outra variável global (ex: conta, tenant), crie um novo context processor.
    - Este padrão é obrigatório para garantir isolamento multi-tenant, consistência e evitar bugs recorrentes.
    """
    """
    Regra de desenvolvimento para contexto de empresa:
    - A variável 'empresa' deve ser sempre injetada no contexto dos templates via context processor (empresa_context), nunca manualmente nas views.
    - A empresa exibida deve ser explicitamente selecionada pelo usuário (armazenada na sessão como 'empresa_id'). Não deve haver fallback automático para a primeira empresa cadastrada.
    - Os templates devem usar apenas {{ empresa }} para exibir informações da empresa, e tratar o caso em que 'empresa' é None (exibindo alerta ou bloqueando navegação).
    - O cabeçalho padrão deve ser incluído via {% include 'layouts/base_header.html' %}.
    - Nunca defina manualmente o nome da empresa ou o título em templates filhos; sempre utilize o contexto global e o template base para garantir consistência visual e semântica.
    """
    empresas_cadastradas = Empresa.objects.all().order_by('nome_fantasia', 'nome')
    empresa_id = request.session.get('empresa_id')
    empresa = None
    if empresa_id:
        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            # Empresa foi deletada ou ID inválido - limpar da sessão
            request.session.pop('empresa_id', None)
    return {
        'empresas_cadastradas': empresas_cadastradas,
        'empresa': empresa,
        'empresa_context_error': None,
    }

def usuario_context(request):
    """
    DIRETRIZ OBRIGATÓRIA: Contexto de Permissões do Usuário
    --------------------------------------------------------
    - Injeta informações de permissão do usuário atual no contexto de todos os templates.
    - 'usuario_admin': indica se o usuário tem role='admin' na conta ativa atual.
    - Usado para controlar visibilidade de links/funcionalidades administrativas na UI.
    - Links sem permissão devem estar visíveis mas desabilitados (UX best practice).
    - Fonte: Implementado conforme estratégia de prj_medicos e Nielsen Norman Group Guidelines.
    """
    if request.user.is_authenticated:
        # Verifica se usuário é admin na conta ativa atual
        conta_id = request.session.get('conta_id')
        usuario_admin = False
        
        if conta_id:
            usuario_admin = (
                request.user.is_superuser or 
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
