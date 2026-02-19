"""
Migration 0005 — BootstrapCertificate + RegistroProvisionamento

Adiciona:
  - tds_new_bootstrapcertificate: cert compartilhado gravado na fábrica em todos os devices
  - tds_new_registroprovisionamento: pedido de auto-registro enviado pelo device no 1º boot
"""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tds_new', '0004_certificadodevice_unique_active_cert_constraint'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # =====================================================================
        # BootstrapCertificate
        # =====================================================================
        migrations.CreateModel(
            name='BootstrapCertificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='bootstrapcertificate_criados',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado Por',
                )),
                ('label', models.CharField(
                    max_length=100,
                    verbose_name='Identificação',
                    help_text="Nome/versão deste bootstrap cert (ex: 'Produção 2026')",
                )),
                ('certificate_pem', models.TextField(verbose_name='Certificado PEM')),
                ('private_key_pem', models.TextField(verbose_name='Chave Privada PEM')),
                ('serial_number', models.CharField(max_length=50, unique=True, verbose_name='Serial Number')),
                ('fingerprint_sha256', models.CharField(
                    max_length=95, blank=True, null=True, verbose_name='Fingerprint SHA-256',
                )),
                ('expires_at', models.DateTimeField(verbose_name='Expira em')),
                ('is_active', models.BooleanField(
                    default=True, verbose_name='Ativo',
                    help_text='Apenas um bootstrap cert pode estar ativo por vez.',
                )),
                ('is_revoked', models.BooleanField(default=False, verbose_name='Revogado')),
                ('revoked_at', models.DateTimeField(blank=True, null=True, verbose_name='Revogado em')),
                ('revoke_reason', models.CharField(
                    blank=True, null=True, max_length=30,
                    choices=[
                        ('COMPROMISED', 'Chave privada comprometida/vazada'),
                        ('ROTATION', 'Rotação planejada de certificado'),
                        ('OTHER', 'Outro motivo'),
                    ],
                    verbose_name='Motivo da Revogação',
                )),
                ('revoke_notes', models.TextField(blank=True, null=True, verbose_name='Observações da Revogação')),
            ],
            options={
                'verbose_name': 'Certificado Bootstrap',
                'verbose_name_plural': 'Certificados Bootstrap',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='bootstrapcertificate',
            index=models.Index(fields=['is_active'], name='tds_new_boo_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='bootstrapcertificate',
            index=models.Index(fields=['is_revoked'], name='tds_new_boo_is_revo_idx'),
        ),
        migrations.AddIndex(
            model_name='bootstrapcertificate',
            index=models.Index(fields=['serial_number'], name='tds_new_boo_serial_idx'),
        ),

        # =====================================================================
        # RegistroProvisionamento
        # =====================================================================
        migrations.CreateModel(
            name='RegistroProvisionamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='registroprovisionamento_criados',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado Por',
                )),
                ('mac_address', models.CharField(max_length=17, verbose_name='MAC Address')),
                ('serial_number_device', models.CharField(
                    max_length=50, blank=True, null=True, verbose_name='Serial do Hardware',
                )),
                ('modelo', models.CharField(max_length=50, blank=True, null=True, verbose_name='Modelo')),
                ('fw_version', models.CharField(max_length=30, blank=True, null=True, verbose_name='Versão do Firmware')),
                ('ip_origem', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP de Origem')),
                ('bootstrap_cert', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='registros',
                    to='tds_new.bootstrapcertificate',
                    verbose_name='Bootstrap Cert Utilizado',
                )),
                ('status', models.CharField(
                    max_length=20, default='PENDENTE',
                    choices=[
                        ('PENDENTE', 'Pendente — aguardando alocação pelo admin'),
                        ('ALOCADO', 'Alocado — gateway criado, aguardando cert'),
                        ('PROVISIONADO', 'Provisionado — cert individual emitido e gravado'),
                        ('REJEITADO', 'Rejeitado — device não autorizado'),
                    ],
                    verbose_name='Status',
                )),
                ('gateway', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='registros_provisionamento',
                    to='tds_new.gateway',
                    verbose_name='Gateway Alocado',
                )),
                ('certificado', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='registro_provisionamento',
                    to='tds_new.certificadodevice',
                    verbose_name='Certificado Individual Emitido',
                )),
                ('processado_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='registros_processados',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Processado Por',
                )),
                ('processado_em', models.DateTimeField(blank=True, null=True, verbose_name='Processado Em')),
                ('notas_admin', models.TextField(blank=True, null=True, verbose_name='Notas do Admin')),
            ],
            options={
                'verbose_name': 'Registro de Provisionamento',
                'verbose_name_plural': 'Registros de Provisionamento',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='registroprovisionamento',
            index=models.Index(fields=['mac_address'], name='tds_new_reg_mac_idx'),
        ),
        migrations.AddIndex(
            model_name='registroprovisionamento',
            index=models.Index(fields=['status'], name='tds_new_reg_status_idx'),
        ),
        migrations.AddIndex(
            model_name='registroprovisionamento',
            index=models.Index(fields=['mac_address', 'status'], name='tds_new_reg_mac_sta_idx'),
        ),
    ]
