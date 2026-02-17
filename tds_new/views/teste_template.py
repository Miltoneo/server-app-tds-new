"""
View de teste para debug do template
"""
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tds_new.models import CertificadoDevice, Gateway

@login_required
def teste_template_certificados(request):
    """
    View de teste para verificar qual template está sendo carregado
    """
    certificados = CertificadoDevice.objects.all()[:2]
    
    # Adicionar gateway aos certificados
    for cert in certificados:
        cert.gateway = Gateway.objects.filter(mac=cert.mac_address).first()
    
    context = {
        'certificados': certificados,
        'titulo_pagina': 'TESTE - Certificados',
        'total_validos': 2,
        'total_expirados': 0,
        'total_revogados': 0,
    }
    
    # Renderizar template
    response = render(request, 'admin_sistema/provisionamento/certificados_list.html', context)
    
    # Adicionar header para debug
    html = response.content.decode('utf-8')
    
    # Verificar se tem botão Alocar ou badge Sem GW
    tem_alocar = 'btn-outline-primary' in html and 'Alocar' in html
    tem_sem_gw = 'Sem GW' in html
    
    debug_info = f"""
    <!-- DEBUG INFO -->
    <!-- Timestamps: {__file__} -->
    <!-- Template tem botão Alocar: {tem_alocar} -->
    <!-- Template tem badge Sem GW: {tem_sem_gw} -->
    <!-- -->
    """
    
    html_com_debug = html.replace('</body>', f'{debug_info}</body>')
    
    return HttpResponse(html_com_debug)
