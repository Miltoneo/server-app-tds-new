"""
Forms para CRUD de Gateways e Dispositivos
"""
from django import forms
from django.core.exceptions import ValidationError
import re

from ..models.dispositivos import Gateway, Dispositivo


class GatewayForm(forms.ModelForm):
    """
    Form para criação/edição de Gateway com validações customizadas
    """
    
    class Meta:
        model = Gateway
        fields = [
            'codigo', 'mac', 'nome', 'descricao',
            'latitude', 'longitude', 'qte_max_dispositivos'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: GW001',
                'maxlength': 30
            }),
            'mac': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'aa:bb:cc:dd:ee:ff',
                'pattern': '[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}',
                'maxlength': 17
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome descritivo do gateway',
                'maxlength': 100
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '-23.550520',
                'step': '0.000001'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '-46.633308',
                'step': '0.000001'
            }),
            'qte_max_dispositivos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 32,
                'value': 8
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.conta = kwargs.pop('conta', None)
        super().__init__(*args, **kwargs)
        
        # Campos obrigatórios
        self.fields['codigo'].required = True
        self.fields['mac'].required = True
        self.fields['nome'].required = True
        
        # Campos opcionais
        self.fields['descricao'].required = False
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        
        # Help texts
        self.fields['mac'].help_text = 'Formato: aa:bb:cc:dd:ee:ff (hexadecimal minúsculo)'
        self.fields['qte_max_dispositivos'].help_text = 'Capacidade máxima de dispositivos (1-32)'
    
    def clean_mac(self):
        """
        Valida formato do MAC address e converte para lowercase
        """
        mac = self.cleaned_data.get('mac', '').strip()
        
        if mac:
            # Validar formato
            mac_pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
            if not re.match(mac_pattern, mac):
                raise ValidationError(
                    'Formato inválido. Use o padrão aa:bb:cc:dd:ee:ff (hexadecimal com dois dígitos separados por :)'
                )
            
            # Padronizar para lowercase
            mac = mac.lower()
            
            # Validar unicidade dentro da conta
            qs = Gateway.objects.filter(conta=self.conta, mac=mac)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f'Gateway com MAC address {mac} já existe nesta conta'
                )
        
        return mac
    
    def clean_codigo(self):
        """
        Valida unicidade do código dentro da conta
        """
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        
        if codigo:
            qs = Gateway.objects.filter(conta=self.conta, codigo=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f'Gateway com código {codigo} já existe nesta conta'
                )
        
        return codigo
    
    def save(self, commit=True):
        """
        Salva o gateway vinculado à conta
        """
        gateway = super().save(commit=False)
        
        if self.conta:
            gateway.conta = self.conta
        
        if commit:
            gateway.save()
        
        return gateway


class DispositivoForm(forms.ModelForm):
    """
    Form para criação/edição de Dispositivo com validações condicionais
    """
    
    class Meta:
        model = Dispositivo
        fields = [
            'gateway', 'codigo', 'nome', 'descricao', 'tipo',
            'slave_id', 'register_modbus', 'modo', 'status',
            'val_alarme_dia', 'val_alarme_mes'
        ]
        widgets = {
            'gateway': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: D01',
                'maxlength': 20
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome descritivo do dispositivo',
                'maxlength': 100
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'slave_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 247,
                'placeholder': '1-247 (obrigatório para MEDIDOR)'
            }),
            'register_modbus': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 65535,
                'placeholder': '1-65535 (obrigatório para MEDIDOR)'
            }),
            'modo': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'val_alarme_dia': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': 'Opcional'
            }),
            'val_alarme_mes': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'placeholder': 'Opcional'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.conta = kwargs.pop('conta', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar gateways apenas da conta ativa
        if self.conta:
            self.fields['gateway'].queryset = Gateway.objects.filter(
                conta=self.conta,
                is_active=True
            ).order_by('codigo')
        
        # Campos obrigatórios
        self.fields['gateway'].required = True
        self.fields['codigo'].required = True
        self.fields['nome'].required = True
        self.fields['tipo'].required = True
        
        # Campos condicionalmente obrigatórios (validados em clean())
        self.fields['slave_id'].required = False
        self.fields['register_modbus'].required = False
        
        # Campos opcionais
        self.fields['descricao'].required = False
        self.fields['val_alarme_dia'].required = False
        self.fields['val_alarme_mes'].required = False
        
        # Help texts
        self.fields['tipo'].help_text = 'MEDIDOR exige slave_id e register_modbus'
    
    def clean_codigo(self):
        """
        Valida unicidade do código dentro do gateway
        """
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        gateway = self.cleaned_data.get('gateway')
        
        if codigo and gateway:
            qs = Dispositivo.objects.filter(gateway=gateway, codigo=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f'Dispositivo com código {codigo} já existe neste gateway'
                )
        
        return codigo
    
    def clean(self):
        """
        Validações customizadas e condicionais
        """
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        slave_id = cleaned_data.get('slave_id')
        register_modbus = cleaned_data.get('register_modbus')
        gateway = cleaned_data.get('gateway')
        
        # Validar campos obrigatórios para tipo=MEDIDOR
        if tipo == 'MEDIDOR':
            if not slave_id:
                self.add_error('slave_id', 'Obrigatório para dispositivos do tipo MEDIDOR')
            if not register_modbus:
                self.add_error('register_modbus', 'Obrigatório para dispositivos do tipo MEDIDOR')
        
        # Validar capacidade do gateway
        if gateway and not self.instance.pk:  # Apenas ao criar novo dispositivo
            dispositivos_ativos = Dispositivo.objects.filter(
                gateway=gateway,
                status='ATIVO'
            ).count()
            
            if dispositivos_ativos >= gateway.qte_max_dispositivos:
                raise ValidationError({
                    'gateway': f'Gateway {gateway.codigo} já atingiu a capacidade máxima de {gateway.qte_max_dispositivos} dispositivos'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Salva o dispositivo vinculado à conta
        """
        dispositivo = super().save(commit=False)
        
        if self.conta:
            dispositivo.conta = self.conta
        
        if commit:
            dispositivo.save()
        
        return dispositivo
