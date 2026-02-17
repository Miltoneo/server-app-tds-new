"""
Formulários de autenticação com reCAPTCHA - TDS New
Implementa proteção contra bots e brute force attacks

Baseado em: server-app-construtora/construtora/forms/auth.py
Criado em: 17/02/2026
"""

import logging
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

logger = logging.getLogger('tds_new.auth')


class SecureLoginForm(AuthenticationForm):
    """
    Formulário de login com proteção camadas:
    
    1. CAPTCHA obrigatório (sempre ativo - melhor prática de segurança)
    2. Rate limiting via django-axes (bloqueio após 5 tentativas)
    3. Bloqueio de 30 minutos após limite excedido
    
    Segue padrão de segurança do Google, Microsoft, GitHub e AWS:
    - CAPTCHA desde a primeira tentativa
    - Proteção total contra bots
    - Fluxo simples e transparente
    
    Uso:
        form = SecureLoginForm(request, data=request.POST)
    """
    
    # Mensagens de erro customizadas
    error_messages = {
        'invalid_login': 'Email ou senha incorretos.',
        'inactive': 'Esta conta está inativa.',
        'required': 'Este campo é obrigatório.',
    }
    
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-callback': 'onCaptchaSuccess',
                'data-expired-callback': 'onCaptchaExpired',
            }
        ),
        required=True,  # ⭐ SEMPRE obrigatório
        label='Verificação de Segurança',
        error_messages={
            'required': 'Complete a verificação de segurança.',
            'invalid': 'Verificação de segurança inválida. Tente novamente.',
        }
    )
    
    def __init__(self, request=None, *args, **kwargs):
        """
        Inicializa o form com request como primeiro argumento posicional.
        
        Args:
            request: HttpRequest object (obrigatório para django-axes)
            *args: Argumentos posicionais adicionais
            **kwargs: Argumentos nomeados (data, initial, etc)
        """
        # ⚠️ CRÍTICO: AuthenticationForm espera request como primeiro argumento
        super().__init__(request, *args, **kwargs)
        
        # Personalizar widgets dos campos padrão
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'seu-email@exemplo.com',
            'autofocus': True
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Sua senha'
        })
        
        # CAPTCHA sempre está presente e obrigatório - sem lógica condicional
    
    def clean(self):
        """
        Sobrescreve clean() para passar request ao authenticate(),
        permitindo que django-axes rastreie tentativas via signals.
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            from django.contrib.auth import authenticate
            
            logger.info(f"[FORM] Tentativa de autenticação para: {username}")
            
            # ⭐ CRÍTICO: Passa request= como KEYWORD argument para disparar signals do axes
            self.user_cache = authenticate(
                request=self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                # Adiciona erro personalizado diretamente
                raise forms.ValidationError(
                    'Credenciais inválidas. Verifique seu email e senha.',
                    code='invalid_login'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
