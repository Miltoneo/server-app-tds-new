"""
Forms para gestão de Gateways IoT - TDS New
"""

from django import forms
from django.core.exceptions import ValidationError
from tds_new.models import Gateway
import re


class GatewayForm(forms.ModelForm):
    """
    Form para criação e edição de Gateways
    
    Validações:
    - MAC address no formato aa:bb:cc:dd:ee:ff
    - Código único dentro da conta
    - Capacidade máxima entre 1 e 32 dispositivos
    """
    
    class Meta:
        model = Gateway
        fields = [
            'codigo',
            'mac',
            'nome',
            'descricao',
            'latitude',
            'longitude',
            'qte_max_dispositivos',
            'firmware_version',
        ]
        
        labels = {
            'codigo': 'Código',
            'mac': 'MAC Address',
            'nome': 'Nome do Gateway',
            'descricao': 'Descrição',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'qte_max_dispositivos': 'Capacidade Máxima (Dispositivos)',
            'firmware_version': 'Versão do Firmware',
        }
        
        help_texts = {
            'codigo': 'Código único do gateway (ex: GW001, GATEWAY_SEDE)',
            'mac': 'Formato: aa:bb:cc:dd:ee:ff (usado como identificador MQTT)',
            'nome': 'Nome descritivo do gateway',
            'descricao': 'Informações adicionais sobre localização ou uso',
            'latitude': 'Coordenada geográfica (ex: -23.550520)',
            'longitude': 'Coordenada geográfica (ex: -46.633308)',
            'qte_max_dispositivos': 'Número máximo de dispositivos conectados (padrão: 8)',
            'firmware_version': 'Versão do firmware instalado (ex: 1.0.0)',
        }
        
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GW001',
                'maxlength': 30,
            }),
            'mac': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'aa:bb:cc:dd:ee:ff',
                'pattern': '[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}',
                'maxlength': 17,
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Gateway Sede Principal',
                'maxlength': 100,
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional do gateway...',
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': '-23.550520',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': '-46.633308',
            }),
            'qte_max_dispositivos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 32,
                'value': 8,
            }),
            'firmware_version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1.0.0',
                'maxlength': 20,
            }),
        }
    
    def clean_mac(self):
        """
        Valida e padroniza o MAC address
        
        Returns:
            str: MAC address em lowercase
        
        Raises:
            ValidationError: se formato inválido
        """
        mac = self.cleaned_data.get('mac')
        
        if not mac:
            raise ValidationError('MAC address é obrigatório')
        
        # Validar formato
        mac_pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
        if not re.match(mac_pattern, mac):
            raise ValidationError(
                'Formato inválido. Use o padrão aa:bb:cc:dd:ee:ff (hexadecimal com dois dígitos separados por :)'
            )
        
        # Padronizar para lowercase
        mac = mac.lower()
        
        return mac
    
    def clean_codigo(self):
        """
        Valida código único
        
        Returns:
            str: Código em uppercase
        
        Raises:
            ValidationError: se código já existir na conta
        """
        codigo = self.cleaned_data.get('codigo')
        
        if not codigo:
            raise ValidationError('Código é obrigatório')
        
        # Padronizar para uppercase
        codigo = codigo.upper().strip()
        
        return codigo
    
    def clean_qte_max_dispositivos(self):
        """
        Valida capacidade máxima
        
        Returns:
            int: Capacidade entre 1 e 32
        
        Raises:
            ValidationError: se fora do intervalo
        """
        qte = self.cleaned_data.get('qte_max_dispositivos')
        
        if qte is None:
            qte = 8  # Default
        
        if qte < 1 or qte > 32:
            raise ValidationError('Capacidade deve estar entre 1 e 32 dispositivos')
        
        return qte


class GatewayFilterForm(forms.Form):
    """
    Form para filtros de busca de Gateways
    """
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('nunca_conectado', 'Nunca Conectado'),
    ]
    
    busca = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código, nome ou MAC...',
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        label='Status',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    capacidade_min = forms.IntegerField(
        required=False,
        label='Capacidade mínima',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'placeholder': '0',
        })
    )
