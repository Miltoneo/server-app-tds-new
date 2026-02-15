"""
Modelos base do TDS New

Sistema multi-tenant para telemetria e monitoramento IoT.

Modelos:
- CustomUser: Modelo de usuário customizado com autenticação por email
- Conta: Modelo de tenant para isolamento multi-tenant
- ContaMembership: Relacionamento User ↔ Conta com controle de acesso (roles)

Referência: server-app-construtora/construtora/models/base.py
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.exceptions import ValidationError


# =============================================================================
# MIXINS PARA CONTROLE DE AUDITORIA
# =============================================================================

class BaseTimestampMixin(models.Model):
    """Mixin para campos de controle de timestamp"""
    class Meta:
        abstract = True
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Atualizado em"
    )


class BaseCreatedByMixin(models.Model):
    """Mixin para campo created_by"""
    class Meta:
        abstract = True
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_criados',
        verbose_name="Criado Por"
    )


class BaseAuditMixin(BaseTimestampMixin, BaseCreatedByMixin):
    """Mixin completo de auditoria"""
    class Meta:
        abstract = True


# =============================================================================
# MANAGER CUSTOMIZADO PARA USUÁRIO
# =============================================================================

class CustomUserManager(UserManager):
    """
    Manager customizado para criação de usuários.
    Usa email como identificador principal e preenche username automaticamente.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Cria e salva um usuário com email como identificador principal.
        Username é preenchido automaticamente com o email.
        """
        if not email:
            raise ValueError('O email é obrigatório')
        
        email = self.normalize_email(email)
        
        # Preenche username com email se não informado
        if not extra_fields.get('username'):
            extra_fields['username'] = email
        
        extra_fields.setdefault('is_active', True)
        
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # Senha não utilizável até ser definida
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Cria um superusuário com todas as permissões"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        # Preenche username com email se não informado
        if not extra_fields.get('username'):
            extra_fields['username'] = email
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')
        
        return self.create_user(email=email, password=password, **extra_fields)


# =============================================================================
# MODELO DE USUÁRIO CUSTOMIZADO
# =============================================================================

class CustomUser(AbstractUser):
    """
    Modelo de usuário customizado.
    
    - Autenticação por email (não por username)
    - Username é preenchido automaticamente com email
    - Suporta sistema de convites via token
    """
    
    objects = CustomUserManager()
    
    class Meta:
        db_table = 'customUser'
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
    
    email = models.EmailField(
        'e-mail address', 
        unique=True,
        help_text="Email do usuário (usado para login)"
    )
    
    invite_token = models.CharField(
        'Token de convite', 
        max_length=64, 
        blank=True, 
        null=True,
        help_text="Token usado no processo de convite de novos usuários"
    )
    
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        unique=False,
        verbose_name='username',
        help_text="Username (preenchido automaticamente com email)"
    )
    
    # Define email como campo de autenticação
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Remove username dos campos obrigatórios
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Retorna nome completo ou email se nome não informado"""
        full_name = super().get_full_name()
        return full_name.strip() if full_name.strip() else self.email
    
    def get_short_name(self):
        """Retorna primeiro nome ou email"""
        if self.first_name:
            return self.first_name
        return self.email.split('@')[0]


# =============================================================================
# MODELO DE CONTA (TENANT)
# =============================================================================

class Conta(BaseAuditMixin):
    """
    Modelo de Conta (Tenant) para isolamento multi-tenant.
    
    Cada conta representa uma organização/empresa independente no sistema.
    Todos os dados (dispositivos, leituras, etc.) são isolados por conta.
    """
    
    class Meta:
        db_table = 'conta'
        verbose_name = "Conta"
        verbose_name_plural = "Contas"
        ordering = ['name']
    
    name = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name="Nome",
        help_text="Nome da conta/organização"
    )
    
    cnpj = models.CharField(
        max_length=32, 
        blank=True, 
        null=True,
        verbose_name="CNPJ",
        help_text="CNPJ da organização (opcional)"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Conta ativa no sistema"
    )
    
    def __str__(self):
        return self.name
    
    def get_total_members(self):
        """Retorna total de membros ativos na conta"""
        return self.memberships.filter(is_active=True).count()
    
    def get_admins(self):
        """Retorna todos os administradores da conta"""
        return self.memberships.filter(role='admin', is_active=True)


# =============================================================================
# MODELO DE MEMBERSHIP (RELACIONAMENTO USER ↔ CONTA)
# =============================================================================

class ContaMembership(BaseAuditMixin):
    """
    Relacionamento entre User e Conta com controle de acesso.
    
    Um usuário pode pertencer a múltiplas contas com diferentes roles.
    Cada membership define o nível de acesso do usuário na conta.
    """
    
    class Meta:
        db_table = 'conta_membership'
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
        unique_together = ('conta', 'user')
        ordering = ['conta', 'user']
        indexes = [
            models.Index(fields=['conta', 'user']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('editor', 'Editor'),
        ('viewer', 'Visualizador'),
    ]
    
    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        related_name='memberships',
        verbose_name="Conta"
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='conta_memberships',
        verbose_name="Usuário"
    )
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='viewer',
        verbose_name="Papel",
        help_text="Nível de acesso do usuário na conta"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Membership ativo"
    )
    
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Adesão"
    )
    
    def __str__(self):
        return f"{self.user.email} - {self.conta.name} ({self.get_role_display()})"
    
    def clean(self):
        """Validação customizada"""
        # Garante que conta e user estão ativos
        if not self.conta.is_active:
            raise ValidationError(
                {'conta': 'Não é possível criar membership em conta inativa'}
            )
        if not self.user.is_active:
            raise ValidationError(
                {'user': 'Não é possível criar membership com usuário inativo'}
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_admin(self):
        """Verifica se o usuário é admin da conta"""
        return self.role == 'admin' and self.is_active
    
    def can_edit(self):
        """Verifica se o usuário pode editar na conta"""
        return self.role in ['admin', 'editor'] and self.is_active
    
    def can_view(self):
        """Verifica se o usuário pode visualizar dados da conta"""
        return self.is_active


# =============================================================================
# MANAGER PARA MODELOS COM ISOLAMENTO POR CONTA
# =============================================================================

class ContaScopedManager(models.Manager):
    """
    Manager que filtra automaticamente por conta (tenant).
    
    Facilita consultas isoladas por conta sem precisar filtrar manualmente.
    """
    
    def get_queryset(self):
        """Retorna queryset padrão sem filtro automático"""
        return super().get_queryset()
    
    def for_conta(self, conta):
        """Filtra por uma conta específica"""
        return super().get_queryset().filter(conta=conta)
    
    def for_conta_id(self, conta_id):
        """Filtra por ID de conta"""
        return super().get_queryset().filter(conta_id=conta_id)


# =============================================================================
# MODELO BASE PARA ISOLAMENTO MULTI-TENANT
# =============================================================================

class SaaSBaseModel(BaseAuditMixin):
    """
    Modelo base abstrato para todos os modelos que precisam de isolamento por conta.
    
    Garante que todo registro está vinculado a uma conta (tenant).
    Inclui campos de auditoria (created_at, updated_at, created_by).
    """
    
    class Meta:
        abstract = True
    
    conta = models.ForeignKey(
        Conta, 
        on_delete=models.CASCADE, 
        null=False,
        verbose_name="Conta"
    )
    
    objects = ContaScopedManager()
    
    def save(self, *args, **kwargs):
        """Valida que conta foi informada antes de salvar"""
        if not self.conta_id:
            raise ValueError(
                f"{self.__class__.__name__} requer uma conta (tenant). "
                "Defina o campo 'conta' antes de salvar."
            )
        super().save(*args, **kwargs)

