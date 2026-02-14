"""
Middleware para isolamento de tenant (SaaS Multi-tenancy)
Garante que todos os dados sejam filtrados por conta/tenant
"""
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from tds_new.models import Conta, ContaMembership

# Storage global para a conta atual (thread-safe)
import threading
_current_account_storage = threading.local()


def get_current_account():
    """
    Retorna a conta atualmente ativa no contexto da requisição
    """
    return getattr(_current_account_storage, 'conta', None)


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware que garante o isolamento de dados por tenant (conta)
    
    Funcionalidades:
    1. Verifica se o usuário tem acesso à conta selecionada
    2. Define a conta ativa na sessão
    3. Filtra automaticamente todos os dados por conta
    4. Redireciona para seleção de conta se necessário
    
    Uso nas views:
    - request.conta_ativa: Conta ativa do usuário
    - request.usuario_conta: ContaMembership do usuário
    """
    
    def process_request(self, request):
        # URLs que não precisam de tenant (usar caminhos diretos é mais confiável)
        exempt_paths = [
            '/admin/',
            '/tds_new/auth/',
            '/tds_new/auth/login/',
            '/tds_new/auth/logout/',
            '/tds_new/auth/select-account/',
            '/tds_new/auth/license-expired/',
            '/tds_new/auth/register/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        # Verifica se a URL atual está na lista de exceções
        if any(request.path.startswith(path) for path in exempt_paths):
            return None
            
        # Se usuário não está autenticado, redireciona para login
        if not request.user.is_authenticated:
            return redirect('/tds_new/auth/login/')
            
        # Tenta obter a conta ativa da sessão
        conta_id = request.session.get('conta_ativa_id')
        
        if conta_id:
            try:
                # Verifica se a conta existe e o usuário tem acesso
                conta = Conta.objects.get(id=conta_id)
                usuario_conta = ContaMembership.objects.get(
                    user=request.user, 
                    conta=conta,
                    is_active=True
                )
                
                # Define a conta ativa no request para uso nas views
                request.conta_ativa = conta
                request.usuario_conta = usuario_conta
                
                # Define a conta global para acesso nas views
                _current_account_storage.conta = conta
                
                return None
                
            except (Conta.DoesNotExist, ContaMembership.DoesNotExist):
                # Remove conta inválida da sessão
                if 'conta_ativa_id' in request.session:
                    del request.session['conta_ativa_id']
                messages.error(request, 'Acesso negado à conta selecionada.')
        
        # Se chegou aqui, precisa selecionar uma conta
        return redirect('/tds_new/auth/select-account/')


class LicenseValidationMiddleware(MiddlewareMixin):
    """
    Middleware que valida se a licença da conta está ativa
    
    NOTA: Este middleware verifica a existência e validade da licença.
    Na implementação futura (Week 8), conectar com shared.assinaturas.
    """
    
    def process_request(self, request):
        # URLs que não precisam de validação de licença
        exempt_paths = [
            '/admin/',
            '/tds_new/auth/login/',
            '/tds_new/auth/logout/',
            '/tds_new/auth/select-account/',
            '/tds_new/auth/license-expired/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(path) for path in exempt_paths):
            return None
            
        # Verifica se há conta ativa
        if hasattr(request, 'conta_ativa'):
            conta = request.conta_ativa
            
            # TODO: Week 8 - Integrar com shared.assinaturas
            # Por enquanto, apenas verifica se conta está ativa
            if not conta.is_active:
                messages.error(
                    request, 
                    f'Conta {conta.name} está inativa. Entre em contato com o suporte.'
                )
                return redirect('/tds_new/auth/license-expired/')
        
        return None


class SessionDebugMiddleware(MiddlewareMixin):
    """
    Middleware para debug de sessão em desenvolvimento
    Remove em produção
    """
    
    def process_request(self, request):
        import logging
        from django.conf import settings
        
        if settings.DEBUG:
            logger = logging.getLogger('tds_new.session')
            logger.debug(f"Path: {request.path}")
            logger.debug(f"User: {request.user}")
            logger.debug(f"Session keys: {list(request.session.keys())}")
            if hasattr(request, 'conta_ativa'):
                logger.debug(f"Conta ativa: {request.conta_ativa}")
        
        return None
