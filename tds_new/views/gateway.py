"""
Views para gestão de Gateways IoT - TDS New

Implements:
- GatewayListView: Lista paginada com filtros
- GatewayCreateView: Criação de gateway
- GatewayUpdateView: Edição de gateway
- GatewayDeleteView: Exclusão com verificação de dispositivos
- GatewayDetailView: Detalhes + lista de dispositivos
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count, F
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from tds_new.models import Gateway, Dispositivo
from tds_new.forms.gateway import GatewayForm, GatewayFilterForm


class GatewayListView(LoginRequiredMixin, ListView):
    """
    Lista de gateways com paginação e filtros
    
    Filtros disponíveis:
    - busca: Código, nome, MAC
    - status: ONLINE, OFFLINE, NUNCA_CONECTADO
    - capacidade_min: Capacidade disponível mínima
    """
    model = Gateway
    template_name = 'tds_new/gateway/list.html'
    context_object_name = 'gateways'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Filtra por conta ativa e aplica filtros de busca
        
        Returns:
            QuerySet: Gateways filtrados e anotados
        """
        conta = self.request.conta_ativa
        queryset = Gateway.objects.filter(conta=conta).annotate(
            dispositivos_ativos=Count('dispositivo', filter=Q(dispositivo__status='ATIVO'))
        ).order_by('-created_at')
        
        # Aplicar filtros
        form = GatewayFilterForm(self.request.GET)
        
        if form.is_valid():
            busca = form.cleaned_data.get('busca')
            if busca:
                queryset = queryset.filter(
                    Q(codigo__icontains=busca) |
                    Q(nome__icontains=busca) |
                    Q(mac__icontains=busca)
                )
            
            status = form.cleaned_data.get('status')
            if status == 'online':
                queryset = queryset.filter(is_online=True)
            elif status == 'offline':
                queryset = queryset.filter(is_online=False, last_seen__isnull=False)
            elif status == 'nunca_conectado':
                queryset = queryset.filter(is_online=False, last_seen__isnull=True)
            
            capacidade_min = form.cleaned_data.get('capacidade_min')
            if capacidade_min is not None:
                queryset = queryset.annotate(
                    capacidade_disponivel_calc=F('qte_max_dispositivos') - F('dispositivos_ativos')
                ).filter(capacidade_disponivel_calc__gte=capacidade_min)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Adiciona formulário de filtros e estatísticas ao contexto
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        conta = self.request.conta_ativa
        
        # Formulário de filtros
        context['filter_form'] = GatewayFilterForm(self.request.GET)
        
        # Estatísticas gerais
        gateways = Gateway.objects.filter(conta=conta)
        context['total_gateways'] = gateways.count()
        context['gateways_online'] = gateways.filter(is_online=True).count()
        context['gateways_offline'] = gateways.filter(is_online=False, last_seen__isnull=False).count()
        
        # Título da página
        context['titulo_pagina'] = 'Gateways IoT'
        
        return context


class GatewayCreateView(LoginRequiredMixin, CreateView):
    """
    Criação de novo gateway
    
    Configura automaticamente:
    - conta: Conta ativa da sessão
    - created_by: Usuário logado
    """
    model = Gateway
    form_class = GatewayForm
    template_name = 'tds_new/gateway/form.html'
    success_url = reverse_lazy('tds_new:gateway_list')
    
    def get_form_kwargs(self):
        """
        Passa conta ativa para o form
        
        Returns:
            dict: Kwargs do form
        """
        kwargs = super().get_form_kwargs()
        kwargs['conta'] = self.request.conta_ativa
        return kwargs
    
    def form_valid(self, form):
        """
        Configura campos automáticos antes de salvar
        
        Args:
            form: Form válido
            
        Returns:
            HttpResponse: Redirect para success_url
        """
        gateway = form.save(commit=False)
        gateway.conta = self.request.conta_ativa
        gateway.created_by = self.request.user
        gateway.save()
        
        messages.success(
            self.request,
            f'Gateway {gateway.codigo} criado com sucesso!'
        )
        
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona título da página ao contexto
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Novo Gateway'
        context['form_action'] = 'Criar'
        return context


class GatewayUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edição de gateway existente
    
    Validações:
    - Gateway pertence à conta ativa
    - Não permite alterar conta
    """
    model = Gateway
    form_class = GatewayForm
    template_name = 'tds_new/gateway/form.html'
    success_url = reverse_lazy('tds_new:gateway_list')
    
    def get_queryset(self):
        """
        Filtra por conta ativa (multi-tenant)
        
        Returns:
            QuerySet: Gateways da conta ativa
        """
        conta = self.request.conta_ativa
        return Gateway.objects.filter(conta=conta)
    
    def get_form_kwargs(self):
        """
        Passa conta ativa para o form
        
        Returns:
            dict: Kwargs do form
        """
        kwargs = super().get_form_kwargs()
        kwargs['conta'] = self.request.conta_ativa
        return kwargs
    
    def form_valid(self, form):
        """
        Salva alterações do gateway
        
        Args:
            form: Form válido
            
        Returns:
            HttpResponse: Redirect para success_url
        """
        gateway = form.save()
        
        messages.success(
            self.request,
            f'Gateway {gateway.codigo} atualizado com sucesso!'
        )
        
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona título da página ao contexto
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f'Editar Gateway {self.object.codigo}'
        context['form_action'] = 'Salvar'
        return context


class GatewayDeleteView(LoginRequiredMixin, DeleteView):
    """
    Exclusão de gateway
    
    Validações:
    - Gateway pertence à conta ativa
    - Verifica se possui dispositivos vinculados
    """
    model = Gateway
    template_name = 'tds_new/gateway/confirm_delete.html'
    success_url = reverse_lazy('tds_new:gateway_list')
    
    def get_queryset(self):
        """
        Filtra por conta ativa (multi-tenant)
        
        Returns:
            QuerySet: Gateways da conta ativa
        """
        conta = self.request.conta_ativa
        return Gateway.objects.filter(conta=conta)
    
    def post(self, request, *args, **kwargs):
        """
        Valida antes de excluir
        
        Verifica se gateway possui dispositivos vinculados
        
        Returns:
            HttpResponse: Redirect ou renderização do form com erros
        """
        self.object = self.get_object()
        
        # Verificar dispositivos vinculados
        dispositivos_count = Dispositivo.objects.filter(gateway=self.object).count()
        
        if dispositivos_count > 0:
            messages.error(
                request,
                f'Não é possível excluir o gateway {self.object.codigo}. '
                f'Existe(m) {dispositivos_count} dispositivo(s) vinculado(s). '
                f'Remova ou transfira os dispositivos antes de excluir o gateway.'
            )
            return redirect('tds_new:gateway_detail', pk=self.object.pk)
        
        # Pode excluir
        messages.success(
            request,
            f'Gateway {self.object.codigo} excluído com sucesso!'
        )
        
        return super().post(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações sobre dispositivos vinculados
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f'Excluir Gateway {self.object.codigo}'
        context['dispositivos_count'] = Dispositivo.objects.filter(gateway=self.object).count()
        return context


class GatewayDetailView(LoginRequiredMixin, DetailView):
    """
    Detalhes do gateway
    
    Exibe:
    - Informações do gateway
    - Status de conexão
    - Lista de dispositivos vinculados
    - Estatísticas de capacidade
    """
    model = Gateway
    template_name = 'tds_new/gateway/detail.html'
    context_object_name = 'gateway'
    
    def get_queryset(self):
        """
        Filtra por conta ativa (multi-tenant)
        
        Returns:
            QuerySet: Gateways da conta ativa
        """
        conta = self.request.conta_ativa
        return Gateway.objects.filter(conta=conta).annotate(
            dispositivos_ativos=Count('dispositivo', filter=Q(dispositivo__status='ATIVO')),
            dispositivos_total=Count('dispositivo')
        )
    
    def get_context_data(self, **kwargs):
        """
        Adiciona dispositivos vinculados ao contexto
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        
        # Dispositivos do gateway
        context['dispositivos'] = Dispositivo.objects.filter(
            gateway=self.object
        ).order_by('codigo')
        
        # Título da página
        context['titulo_pagina'] = f'Gateway {self.object.codigo}'
        
        return context
