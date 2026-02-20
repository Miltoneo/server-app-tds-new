"""
Formulários de Provisionamento - TDS New

Forms para gestão administrativa de gateways e certificados:
- AlocarGatewayForm:            Alocação/transferência de gateway entre contas
- GerarCertificadoFactoryForm:  Geração de certificado X.509 modo factory
- RevogarCertificadoForm:       Revogação de certificado com motivo
- GerarBootstrapCertForm:       Geração de Bootstrap Certificate para a fábrica
- RevogarBootstrapCertForm:     Revogação de Bootstrap Certificate (emergência)
- ProcessarRegistroForm:        Admin aloca um RegistroProvisionamento pendente
"""

from django import forms
from tds_new.models import Gateway, Conta, CertificadoDevice


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


class GerarCertificadoFactoryForm(forms.Form):
    """
    Formulário de confirmação para geração de certificado X.509 no modo factory.

    Modo factory: o servidor gera o par chave+certificado para gravação física no dispositivo.
    Usar apenas quando o dispositivo não suporta geração de CSR internamente.

    Validações:
    - Gateway deve ter device_id ou MAC preenchido
    - Confirmar se deseja sobrescrever certificado existente
    """

    forcar_renovacao = forms.BooleanField(
        required=False,
        initial=False,
        label="Revogar certificado existente e gerar novo",
        help_text="Marque apenas se quiser substituir um certificado ativo. "
                  "O certificado anterior será revogado automaticamente.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    confirmacao = forms.BooleanField(
        required=True,
        label="Confirmo que este dispositivo será gravado fisicamente",
        help_text="O pacote ZIP gerado deve ser gravado via esptool.py/NVS partition tool.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.gateway = kwargs.pop('gateway', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.gateway and not (self.gateway.device_id or self.gateway.mac):
            raise forms.ValidationError(
                "O gateway não possui device_id nem MAC configurado. "
                "Preencha esses campos antes de gerar o certificado."
            )
        return cleaned_data


class RevogarCertificadoForm(forms.Form):
    """
    Formulário de revogação de certificado X.509.

    Solicita motivo padronizado (REVOKE_REASON_CHOICES) e notas opcionais.
    Após revogação, o admin deve atualizar a CRL no broker MQTT Mosquitto.
    """

    MOTIVO_CHOICES = CertificadoDevice.REVOKE_REASON_CHOICES

    motivo = forms.ChoiceField(
        choices=MOTIVO_CHOICES,
        label="Motivo da Revogação",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    notas = forms.CharField(
        required=False,
        max_length=500,
        label="Observações",
        help_text="Informações adicionais sobre a revogação (opcional).",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ex: Dispositivo extraviado. Substituído por serial XYZ...'
        })
    )

    confirmacao = forms.BooleanField(
        required=True,
        label="Confirmo a revogação deste certificado",
        help_text="Esta ação é irreversível. O dispositivo perderá acesso ao broker MQTT.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


# =============================================================================
# BOOTSTRAP CERTIFICATE
# =============================================================================

class GerarBootstrapCertForm(forms.Form):
    """
    Geração de Bootstrap Certificate para gravação em lote na fábrica.

    O bootstrap cert é compartilhado — todos os devices do lote saem com o mesmo par
    (bootstrap.crt + bootstrap.key). Permite a conexão inicial ao broker apenas para
    o tópico de provisionamento.

    Um novo bootstrap cert desativa automaticamente o anterior.
    """

    label = forms.CharField(
        max_length=100,
        label="Identificação do Lote",
        help_text="Nome descritivo para este bootstrap cert (ex: 'Produção Q1-2026', 'Lote Fevereiro 2026').",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Produção Q1-2026'
        })
    )

    confirmacao = forms.BooleanField(
        required=True,
        label="Confirmo a geração de um novo Bootstrap Certificate",
        help_text=(
            "O bootstrap cert anterior (se ativo) será marcado como inativo. "
            "Devices já provisionados NÃO são afetados."
        ),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class RevogarBootstrapCertForm(forms.Form):
    """
    Revogação de emergência de Bootstrap Certificate.

    ⚠️ Revogar o bootstrap cert impede que devices ainda não provisionados
    se conectem ao broker. Use SOMENTE em caso de comprometimento da chave privada.

    Para rotação planejada (troca de lote), gere um novo bootstrap cert sem revogar.
    """

    MOTIVO_CHOICES = [
        ('COMPROMISED', 'Chave privada comprometida/vazada'),
        ('ROTATION', 'Rotação planejada de certificado'),
        ('OTHER', 'Outro motivo'),
    ]

    motivo = forms.ChoiceField(
        choices=MOTIVO_CHOICES,
        label="Motivo da Revogação",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    notas = forms.CharField(
        required=False,
        max_length=500,
        label="Observações",
        help_text="Descreva as circunstâncias da revogação para fins de auditoria.",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ex: Chave encontrada em repositório público. Revogação imediata.'
        })
    )

    confirmacao = forms.BooleanField(
        required=True,
        label=(
            "Entendo que esta revogação bloqueará TODOS os devices não provisionados "
            "que usam este bootstrap cert"
        ),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


# =============================================================================
# PROCESSAR REGISTRO PENDENTE
# =============================================================================

class ProcessarRegistroForm(forms.Form):
    """
    Admin aloca um RegistroProvisionamento pendente para uma conta.

    Permite:
    - Selecionar a conta destino
    - Criar/selecionar o Gateway para este device
    - Adicionar notas
    """

    conta = forms.ModelChoiceField(
        queryset=Conta.objects.all(),
        label="Conta Destino",
        help_text="Conta à qual este device será vinculado.",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    device_id = forms.CharField(
        max_length=20,
        label="Device ID (MQTT)",
        help_text="Identificador lógico para MQTT (ex: AA0011). Único por conta.",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: AA0011'})
    )

    nome_gateway = forms.CharField(
        max_length=100,
        label="Nome do Gateway",
        help_text="Nome descritivo para identificação na interface.",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Medidor Prédio A'})
    )

    notas = forms.CharField(
        required=False,
        max_length=500,
        label="Notas do Admin",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
