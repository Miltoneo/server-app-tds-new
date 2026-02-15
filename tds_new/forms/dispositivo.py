"""
Forms para gestão de Dispositivos IoT - TDS New
"""

from django import forms
from django.core.exceptions import ValidationError
from tds_new.models import Dispositivo, Gateway
import re


class DispositivoForm(forms.ModelForm):
    """
    Form para criação e edição de Dispositivos
    
    Validações condicionais:
    - tipo=MEDIDOR: slave_id e register_modbus obrigatórios
    - MAC address opcional (formato aa:bb:cc:dd:ee:ff se preenchido)
    - Capacidade do gateway respeitada
    """
    
    class Meta:
        model = Dispositivo
        fields = [
            'gateway',
            'codigo',
            'mac',
            'nome',
            'descricao',
            'tipo',
            'register_modbus',
            'slave_id',
            'modo',
            'status',
            'val_alarme_dia',
            'val_alarme_mes',
            'firmware_version',
        ]
        
        labels = {
            'gateway': 'Gateway',
            'codigo': 'Código',
            'mac': 'MAC Address',
            'nome': 'Nome do Dispositivo',
            'descricao': 'Descrição',
            'tipo': 'Tipo',
            'register_modbus': 'Registro Modbus',
            'slave_id': 'Slave ID (Modbus)',
            'modo': 'Modo de Operação',
            'status': 'Status',
            'val_alarme_dia': 'Alarme Diário',
            'val_alarme_mes': 'Alarme Mensal',
            'firmware_version': 'Versão do Firmware',
        }
        
        help_texts = {
            'gateway': 'Selecione o gateway ao qual o dispositivo está conectado',
            'codigo': 'Código único dentro do gateway (ex: D01, D02)',
            'mac': 'MAC address (opcional - apenas para dispositivos WiFi/Ethernet direto)',
            'nome': 'Nome descritivo do dispositivo',
            'descricao': 'Informações adicionais sobre o dispositivo',
            'tipo': 'Tipo do dispositivo (Medidor requer configuração Modbus)',
            'register_modbus': 'Registro Modbus a ser lido (1-65535) - obrigatório para Medidores',
            'slave_id': 'ID do dispositivo no barramento Modbus (1-247) - obrigatório para Medidores',
            'modo': 'Modo de operação do dispositivo',
            'status': 'Status operacional do dispositivo',
            'val_alarme_dia': 'Valor limite para disparo de alarme diário',
            'val_alarme_mes': 'Valor limite para disparo de alarme mensal',
            'firmware_version': 'Versão do firmware instalado',
        }
        
        widgets = {
            'gateway': forms.Select(attrs={
                'class': 'form-select',
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'D01',
                'maxlength': 20,
            }),
            'mac': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'aa:bb:cc:dd:ee:ff (opcional)',
                'pattern': '[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}',
                'maxlength': 17,
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Medidor de Água - Entrada Principal',
                'maxlength': 100,
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional do dispositivo...',
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleModbusFields()',  # JavaScript para mostrar/ocultar campos Modbus
            }),
            'register_modbus': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 65535,
                'placeholder': '1000',
            }),
            'slave_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 247,
                'placeholder': '1',
            }),
            'modo': forms.Select(attrs={
                'class': 'form-select',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'val_alarme_dia': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '1000.00',
            }),
            'val_alarme_mes': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '30000.00',
            }),
            'firmware_version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1.0.0',
                'maxlength': 20,
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Customiza o queryset de gateway baseado na conta ativa
        """
        conta = kwargs.pop('conta', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas gateways da conta ativa
        if conta:
            self.fields['gateway'].queryset = Gateway.objects.filter(conta=conta)
        
        # Marcar campos opcionais
        self.fields['mac'].required = False
        self.fields['descricao'].required = False
        self.fields['register_modbus'].required = False
        self.fields['slave_id'].required = False
        self.fields['val_alarme_dia'].required = False
        self.fields['val_alarme_mes'].required = False
        self.fields['firmware_version'].required = False
    
    def clean_mac(self):
        """
        Valida e padroniza o MAC address (se preenchido)
        
        Returns:
            str: MAC address em lowercase ou None
        
        Raises:
            ValidationError: se formato inválido
        """
        mac = self.cleaned_data.get('mac')
        
        if not mac:
            return None  # MAC é opcional
        
        # Validar formato
        mac_pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
        if not re.match(mac_pattern, mac):
            raise ValidationError(
                'Formato inválido. Use o padrão aa:bb:cc:dd:ee:ff'
            )
        
        # Padronizar para lowercase
        mac = mac.lower()
        
        return mac
    
    def clean_codigo(self):
        """
        Valida código único dentro do gateway
        
        Returns:
            str: Código em uppercase
        """
        codigo = self.cleaned_data.get('codigo')
        
        if not codigo:
            raise ValidationError('Código é obrigatório')
        
        # Padronizar para uppercase
        codigo = codigo.upper().strip()
        
        return codigo
    
    def clean(self):
        """
        Validações customizadas que dependem de múltiplos campos
        
        Raises:
            ValidationError: para validações de negócio
        """
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        slave_id = cleaned_data.get('slave_id')
        register_modbus = cleaned_data.get('register_modbus')
        gateway = cleaned_data.get('gateway')
        status = cleaned_data.get('status')
        
        # Validação condicional para tipo MEDIDOR (Modbus RTU)
        if tipo == 'MEDIDOR':
            if not slave_id:
                self.add_error('slave_id', 'Slave ID é obrigatório para dispositivos do tipo Medidor (Modbus RTU)')
            elif not (1 <= slave_id <= 247):
                self.add_error('slave_id', 'Slave ID deve estar entre 1 e 247')
            
            if not register_modbus:
                self.add_error('register_modbus', 'Registro Modbus é obrigatório para dispositivos do tipo Medidor')
            elif not (1 <= register_modbus <= 65535):
                self.add_error('register_modbus', 'Registro Modbus deve estar entre 1 e 65535')
        
        # Validar capacidade do gateway (apenas se status = ATIVO)
        if gateway and status == 'ATIVO':
            # Contar dispositivos ativos no gateway (excluindo este se for edição)
            dispositivos_ativos = Dispositivo.objects.filter(
                gateway=gateway,
                status='ATIVO'
            )
            
            if self.instance.pk:
                dispositivos_ativos = dispositivos_ativos.exclude(pk=self.instance.pk)
            
            count = dispositivos_ativos.count()
            
            if count >= gateway.qte_max_dispositivos:
                self.add_error('gateway', 
                    f'Gateway {gateway.codigo} atingiu capacidade máxima '
                    f'({gateway.qte_max_dispositivos} dispositivos ativos). '
                    f'Desative um dispositivo existente ou aumente a capacidade do gateway.')
        
        return cleaned_data


class DispositivoFilterForm(forms.Form):
    """
    Form para filtros de busca de Dispositivos
    """
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ATIVO', 'Ativo'),
        ('INATIVO', 'Inativo'),
        ('MANUTENCAO', 'Manutenção'),
    ]
    
    TIPO_CHOICES = [
        ('', 'Todos'),
        ('MEDIDOR', 'Medidor'),
        ('SENSOR', 'Sensor'),
        ('ATUADOR', 'Atuador'),
    ]
    
    busca = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código, nome ou MAC...',
        })
    )
    
    gateway = forms.ModelChoiceField(
        required=False,
        queryset=Gateway.objects.none(),  # Será definido no __init__
        label='Gateway',
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    tipo = forms.ChoiceField(
        required=False,
        choices=TIPO_CHOICES,
        label='Tipo',
        widget=forms.Select(attrs={
            'class': 'form-select',
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
    
    def __init__(self, *args, **kwargs):
        """
        Customiza o queryset de gateway baseado na conta
        """
        conta = kwargs.pop('conta', None)
        super().__init__(*args, **kwargs)
        
        if conta:
            self.fields['gateway'].queryset = Gateway.objects.filter(conta=conta).order_by('codigo')
