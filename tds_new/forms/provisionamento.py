"""
Formulários de Provisionamento - TDS New

Forms para gestão administrativa de gateways e certificados:
- AlocarGatewayForm: Alocação/transferência de gateway entre contas
- ImportarGatewaysCSVForm: Importação em lote via CSV (planejado)
"""

from django import forms
from tds_new.models import Gateway, Conta


class AlocarGatewayForm(forms.ModelForm):
    """
    Formulário para alocar gateway a uma conta específica
    
    Funcionalidades:
    - Seleção de conta destino (apenas contas ativas)
    - Opção de transferir dispositivos vinculados junto
    - Validações de segurança e integridade
    
    Uso:
        form = AlocarGatewayForm(instance=gateway)
        if form.is_valid():
            gateway = form.save()
    """
    
    transferir_dispositivos = forms.BooleanField(
        required=False,
        initial=True,
        label="Transferir dispositivos vinculados",
        help_text="Se marcado, todos os dispositivos vinculados ao gateway também serão transferidos para a nova conta",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    class Meta:
        model = Gateway
        fields = ['conta']
        widgets = {
            'conta': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            })
        }
        labels = {
            'conta': 'Conta Destino',
        }
        help_texts = {
            'conta': 'Selecione a conta que receberá o gateway e seus certificados',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas contas ativas, ordenadas por nome
        self.fields['conta'].queryset = Conta.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Adicionar placeholder
        self.fields['conta'].empty_label = "Selecione uma conta..."
    
    def clean_conta(self):
        """
        Validação customizada do campo conta
        """
        conta = self.cleaned_data.get('conta')
        
        # Validar se conta está ativa
        if conta and not conta.is_active:
            raise forms.ValidationError(
                "Conta inativa não pode receber gateways. Ative a conta antes de prosseguir."
            )
        
        # Validar se o MAC já existe na conta destino (evitar duplicação)
        if self.instance and self.instance.mac:
            gateway_existente = Gateway.objects.filter(
                conta=conta,
                mac=self.instance.mac
            ).exclude(pk=self.instance.pk).first()
            
            if gateway_existente:
                raise forms.ValidationError(
                    f"Gateway com MAC {self.instance.mac} já existe na conta {conta.name}. "
                    f"Verifique se não há duplicação."
                )
        
        return conta
