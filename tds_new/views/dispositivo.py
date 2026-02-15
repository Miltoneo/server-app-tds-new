"""
Views para gestão de Dispositivos IoT - TDS New

Implements:
- DispositivoListView: Lista paginada com filtros
- DispositivoCreateView: Criação de dispositivo com validação de capacidade
- DispositivoUpdateView: Edição de dispositivo
- DispositivoDeleteView: Exclusão simples (sem dependências complexas)
- DispositivoDetailView: Detalhes + últimas leituras
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from tds_new.models import Dispositivo, Gateway, LeituraDispositivo
from tds_new.forms.dispositivo import DispositivoForm, DispositivoFilterForm


class DispositivoListView(LoginRequiredMixin, ListView):
    """
    Lista de dispositivos com paginação e filtros
    
    Filtros disponíveis:
    - busca: Código, nome, MAC
    - gateway: Gateway específico
    - tipo: MEDIDOR, SENSOR, ATUADOR
    - status: ATIVO, INATIVO, MANUTENCAO
    """
    model = Dispositivo
    template_name = 'tds_new/dispositivo/list.html'
    context_object_name = 'dispositivos'
    paginate_by = 20
    
    def get_queryset(self):
        """
        Filtra por conta ativa (via gateway) e aplica filtros de busca
        
        Returns:
            QuerySet: Dispositivos filtrados
        """
        conta = self.request.session.get('conta')
        queryset = Dispositivo.objects.filter(
            gateway__conta=conta
        ).select_related('gateway').order_by('gateway__codigo', 'codigo')
        
        # Aplicar filtros
        form = DispositivoFilterForm(self.request.GET, conta=conta)
        
        if form.is_valid():
            busca = form.cleaned_data.get('busca')
            if busca:
                queryset = queryset.filter(
                    Q(codigo__icontains=busca) |
                    Q(nome__icontains=busca) |
                    Q(mac__icontains=busca) |
                    Q(gateway__codigo__icontains=busca)
                )
            
            gateway = form.cleaned_data.get('gateway')
            if gateway:
                queryset = queryset.filter(gateway=gateway)
            
            tipo = form.cleaned_data.get('tipo')
            if tipo:
                queryset = queryset.filter(tipo=tipo)
            
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Adiciona formulário de filtros e estatísticas ao contexto
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        conta = self.request.session.get('conta')
        
        # Formulário de filtros
        context['filter_form'] = DispositivoFilterForm(self.request.GET, conta=conta)
        
        # Estatísticas gerais
        dispositivos = Dispositivo.objects.filter(gateway__conta=conta)
        context['total_dispositivos'] = dispositivos.count()
        context['dispositivos_ativos'] = dispositivos.filter(status='ATIVO').count()
        context['dispositivos_online'] = dispositivos.filter(is_online=True).count()
        
        # Título da página
        context['titulo_pagina'] = 'Dispositivos IoT'
        
        return context


class DispositivoCreateView(LoginRequiredMixin, CreateView):
    """
    Criação de novo dispositivo
    
    Validações automáticas:
    - Capacidade do gateway respeitada
    - Validação condicional de Modbus (se tipo=MEDIDOR)
    - created_by configurado automaticamente
    """
    model = Dispositivo
    form_class = DispositivoForm
    template_name = 'tds_new/dispositivo/form.html'
    success_url = reverse_lazy('tds_new:dispositivo_list')
    
    def get_form_kwargs(self):
        """
        Passa conta ativa para o form
        
        Returns:
            dict: Kwargs do form
        """
        kwargs = super().get_form_kwargs()
        kwargs['conta'] = self.request.session.get('conta')
        return kwargs
    
    def form_valid(self, form):
        """
        Configura created_by antes de salvar
        
        Args:
            form: Form válido
            
        Returns:
            HttpResponse: Redirect para success_url
        """
        dispositivo = form.save(commit=False)
        dispositivo.created_by = self.request.user
        dispositivo.save()
        
        messages.success(
            self.request,
            f'Dispositivo {dispositivo.identificador_completo} criado com sucesso!'
        )
        
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona título da página ao contexto
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Novo Dispositivo'
        context['form_action'] = 'Criar'
        return context


class DispositivoUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edição de dispositivo existente
    
    Validações:
    - Dispositivo pertence à conta ativa (via gateway)
    - Não permite alterar gateway se houver leituras
    """
    model = Dispositivo
    form_class = DispositivoForm
    template_name = 'tds_new/dispositivo/form.html'
    success_url = reverse_lazy('tds_new:dispositivo_list')
    
    def get_queryset(self):
        """
        Filtra por conta ativa (multi-tenant via gateway)
        
        Returns:
            QuerySet: Dispositivos da conta ativa
        """
        conta = self.request.session.get('conta')
        return Dispositivo.objects.filter(gateway__conta=conta).select_related('gateway')
    
    def get_form_kwargs(self):
        """
        Passa conta ativa para o form
        
        Returns:
            dict: Kwargs do form
        """
        kwargs = super().get_form_kwargs()
        kwargs['conta'] = self.request.session.get('conta')
        return kwargs
    
    def form_valid(self, form):
        """
        Salva alterações do dispositivo
        
        Args:
            form: Form válido
            
        Returns:
            HttpResponse: Redirect para success_url
        """
        dispositivo = form.save()
        
        messages.success(
            self.request,
            f'Dispositivo {dispositivo.identificador_completo} atualizado com sucesso!'
        )
        
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona título da página ao contexto
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f'Editar Dispositivo {self.object.identificador_completo}'
        context['form_action'] = 'Salvar'
        return context


class DispositivoDeleteView(LoginRequiredMixin, DeleteView):
    """
    Exclusão de dispositivo
    
    Validações:
    - Dispositivo pertence à conta ativa
    - Aviso: Leituras históricas não são excluídas (TimescaleDB read-only)
    """
    model = Dispositivo
    template_name = 'tds_new/dispositivo/confirm_delete.html'
    success_url = reverse_lazy('tds_new:dispositivo_list')
    
    def get_queryset(self):
        """
        Filtra por conta ativa (multi-tenant via gateway)
        
        Returns:
            QuerySet: Dispositivos da conta ativa
        """
        conta = self.request.session.get('conta')
        return Dispositivo.objects.filter(gateway__conta=conta).select_related('gateway')
    
    def post(self, request, *args, **kwargs):
        """
        Exclui dispositivo (leituras históricas permanecem)
        
        Returns:
            HttpResponse: Redirect para success_url
        """
        self.object = self.get_object()
        
        # Aviso sobre leituras históricas
        messages.warning(
            request,
            f'Dispositivo {self.object.identificador_completo} excluído. '
            f'Leituras históricas foram mantidas no banco de dados.'
        )
        
        return super().post(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Adiciona informações sobre leituras ao contexto
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f'Excluir Dispositivo {self.object.identificador_completo}'
        
        # Contar leituras (se TimescaleDB estiver configurado)
        try:
            leituras_count = LeituraDispositivo.objects.filter(dispositivo=self.object).count()
            context['leituras_count'] = leituras_count
        except Exception:
            context['leituras_count'] = None  # TimescaleDB não configurado ainda
        
        return context


class DispositivoDetailView(LoginRequiredMixin, DetailView):
    """
    Detalhes do dispositivo
    
    Exibe:
    - Informações do dispositivo
    - Status de conexão
    - Gateway pai
    - Últimas 10 leituras (se TimescaleDB configurado)
    - Estatísticas de consumo
    """
    model = Dispositivo
    template_name = 'tds_new/dispositivo/detail.html'
    context_object_name = 'dispositivo'
    
    def get_queryset(self):
        """
        Filtra por conta ativa (multi-tenant via gateway)
        
        Returns:
            QuerySet: Dispositivos da conta ativa
        """
        conta = self.request.session.get('conta')
        return Dispositivo.objects.filter(gateway__conta=conta).select_related('gateway')
    
    def get_context_data(self, **kwargs):
        """
        Adiciona leituras recentes ao contexto
        
        Returns:
            dict: Contexto da view
        """
        context = super().get_context_data(**kwargs)
        
        # Título da página
        context['titulo_pagina'] = f'Dispositivo {self.object.identificador_completo}'
        
        # Últimas leituras (se TimescaleDB estiver configurado)
        try:
            leituras = LeituraDispositivo.objects.filter(
                dispositivo=self.object
            ).order_by('-time')[:10]
            context['leituras'] = list(leituras)
        except Exception:
            # TimescaleDB não configurado ainda
            context['leituras'] = []
        
        return context
