"""
Migration 0006 — Adiciona csr_pem ao RegistroProvisionamento

Campo para armazenar o CSR (PKCS#10) enviado pelo device no auto-registro.
Quando presente, permite usar gerar_certificado_de_csr() ao processar o registro,
eliminando o armazenamento da chave privada no servidor (Fase 5a do plano PKI).

Gerado manualmente: 2026-02-20
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tds_new', '0005_bootstrapcertificate_registroprovisionamento'),
    ]

    operations = [
        migrations.AddField(
            model_name='registroprovisionamento',
            name='csr_pem',
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name='CSR (PKCS#10)',
                help_text=(
                    'Certificate Signing Request enviado pelo device no auto-registro. '
                    'Quando presente, o cert individual é gerado pelo fluxo CSR (chave privada '
                    'permanece no device). Requer firmware atualizado.'
                ),
            ),
        ),
    ]
