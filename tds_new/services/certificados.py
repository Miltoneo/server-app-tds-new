"""
Serviço de Certificados X.509 — TDS New IoT

Responsabilidade:
  - Assinar CSRs enviados por dispositivos ESP32 (modelo PKI correto)
  - Geração de par chave+certificado no servidor (legacy / factory pre-provisioning)
  - Empacotamento ZIP de provisionamento para gravação no dispositivo
  - Revogação de certificados

Modelo PKI Adotado (CSR):
  1. Dispositivo gera par RSA 2048 internamente via mbedTLS
  2. Dispositivo gera CSR com CN = device_id
  3. Backend recebe apenas o CSR (chave privada NUNCA sai do dispositivo)
  4. Backend assina CSR com CA e retorna SOMENTE o certificado assinado (PEM)
  5. Dispositivo armazena certificado + chave privada na NVS partition 'certs'

Referência: docs/PROVISIONAMENTO_IOT.md — Estratégia 2 (API Sign-CSR)
"""

import io
import os
import zipfile
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from cryptography.x509.oid import ExtendedKeyUsageOID

from django.conf import settings
from django.utils import timezone as django_tz

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEÇÕES
# =============================================================================

class CertificadoServiceError(Exception):
    """Erro base do serviço de certificados"""
    pass


class CANaoConfiguradaError(CertificadoServiceError):
    """CA não encontrada ou não configurada"""
    pass


class CSRInvalidoError(CertificadoServiceError):
    """CSR inválido ou não confiável"""
    pass


class CertificadoJaExistenteError(CertificadoServiceError):
    """Dispositivo já possui certificado ativo"""
    pass


# =============================================================================
# SERVIÇO PRINCIPAL
# =============================================================================

class CertificadoService:
    """
    Serviço para gestão do ciclo de vida de certificados X.509 de dispositivos IoT.

    Uso:
        service = CertificadoService()
        cert = service.gerar_certificado_de_csr(
            device_id='AA0011',
            csr_pem='-----BEGIN CERTIFICATE REQUEST-----...',
            mac_address='aa:bb:cc:dd:ee:ff',
            conta=conta_obj
        )
    """

    def __init__(self):
        self.ca_cert_path = Path(settings.MQTT_CA_CERT_PATH)
        self.ca_key_path = Path(settings.MQTT_CA_KEY_PATH)
        self.ca_key_password = getattr(settings, 'MQTT_CA_KEY_PASSWORD', '') or None
        self.validity_days = getattr(settings, 'DEVICE_CERT_VALIDITY_DAYS', 3650)
        self._ca_cert = None
        self._ca_key = None

    # =========================================================================
    # CARREGAMENTO DA CA
    # =========================================================================

    def _load_ca(self):
        """Carrega certificado e chave privada da CA."""
        if not self.ca_cert_path.exists():
            raise CANaoConfiguradaError(
                f"Certificado da CA não encontrado: {self.ca_cert_path}\n"
                f"Consulte certs/ca/README.md para instruções de geração."
            )
        if not self.ca_key_path.exists():
            raise CANaoConfiguradaError(
                f"Chave privada da CA não encontrada: {self.ca_key_path}\n"
                f"Consulte certs/ca/README.md para instruções de geração."
            )

        with open(self.ca_cert_path, 'rb') as f:
            self._ca_cert = load_pem_x509_certificate(f.read(), default_backend())

        password_bytes = None
        if self.ca_key_password:
            password_bytes = self.ca_key_password.encode('utf-8')

        with open(self.ca_key_path, 'rb') as f:
            self._ca_key = serialization.load_pem_private_key(
                f.read(),
                password=password_bytes,
                backend=default_backend()
            )

        logger.info(
            "[CertificadoService] CA carregada: CN=%s",
            self._ca_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        )

    @property
    def ca_cert(self):
        if self._ca_cert is None:
            self._load_ca()
        return self._ca_cert

    @property
    def ca_key(self):
        if self._ca_key is None:
            self._load_ca()
        return self._ca_key

    # =========================================================================
    # LEITURA DO CERTIFICADO PÚBLICO DA CA
    # =========================================================================

    def get_ca_cert_pem(self) -> str:
        """Retorna o certificado público da CA em formato PEM."""
        return self.ca_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')

    # =========================================================================
    # ASSINATURA DE CSR (Modelo correto — chave gerada no dispositivo)
    # =========================================================================

    def gerar_certificado_de_csr(
        self,
        device_id: str,
        csr_pem: str,
        mac_address: str,
        conta,
        gateway=None,
        forcar_renovacao: bool = False
    ):
        """
        Assina um CSR enviado pelo dispositivo e persiste o CertificadoDevice.

        Modelo PKI correto:
          - Dispositivo gerou o par de chaves RSA internamente (mbedTLS)
          - Dispositivo enviou SOMENTE o CSR (chave privada permanece no dispositivo)
          - Backend assina e retorna SOMENTE o certificado

        Args:
            device_id (str): ID lógico do dispositivo (ex: 'AA0011')
            csr_pem (str): CSR no formato PEM enviado pelo dispositivo
            mac_address (str): MAC address do dispositivo
            conta: Instância do modelo Conta (tenant)
            gateway: Instância do modelo Gateway (opcional)
            forcar_renovacao (bool): Se True, revoga cert existente antes de gerar novo

        Returns:
            CertificadoDevice: Instância do certificado criado/salvo

        Raises:
            CSRInvalidoError: Se o CSR não puder ser carregado ou validado
            CertificadoJaExistenteError: Se já existe cert ativo (use forcar_renovacao=True)
            CANaoConfiguradaError: Se a CA não estiver disponível
        """
        from tds_new.models import CertificadoDevice

        # Verificar se já existe certificado ativo para este device_id
        if not forcar_renovacao:
            cert_existente = CertificadoDevice.objects.filter(
                conta=conta,
                device_id=device_id,
                is_revoked=False
            ).first()
            if cert_existente:
                raise CertificadoJaExistenteError(
                    f"Dispositivo {device_id} já possui certificado ativo (ID={cert_existente.pk}). "
                    f"Use forcar_renovacao=True para revogar e gerar novo."
                )

        # Revogar certificado anterior se solicitado
        if forcar_renovacao:
            certs_anteriores = CertificadoDevice.objects.filter(
                conta=conta,
                device_id=device_id,
                is_revoked=False
            )
            for cert_ant in certs_anteriores:
                cert_ant.revogar(
                    motivo='SUPERSEDED',
                    notas=f'Revogado automaticamente ao gerar novo certificado para {device_id}'
                )
                logger.info(
                    "[CertificadoService] Certificado anterior revogado: ID=%s device_id=%s",
                    cert_ant.pk, device_id
                )

        # Carregar e validar o CSR
        try:
            csr = x509.load_pem_x509_csr(csr_pem.encode('utf-8'), default_backend())
        except Exception as e:
            raise CSRInvalidoError(f"Falha ao carregar CSR: {e}") from e

        if not csr.is_signature_valid:
            raise CSRInvalidoError("Assinatura do CSR é inválida.")

        # Gerar número de série único (128 bits aleatórios)
        serial_number = x509.random_serial_number()

        # Calcular período de validade
        agora = datetime.now(timezone.utc)
        expira_em = agora + timedelta(days=self.validity_days)

        # Construir certificado assinado pela CA
        builder = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(self.ca_cert.subject)
            .public_key(csr.public_key())
            .serial_number(serial_number)
            .not_valid_before(agora)
            .not_valid_after(expira_em)
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
                critical=False
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
                critical=False
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(self.ca_cert.public_key()),
                critical=False
            )
        )

        # Adicionar Subject Alternative Name com device_id e MAC
        san_entries = [x509.DNSName(device_id)]
        builder = builder.add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False
        )

        certificate = builder.sign(self.ca_key, hashes.SHA256(), default_backend())

        # Serializar para PEM
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8')

        # Calcular fingerprint SHA-256
        fingerprint = hashlib.sha256(
            certificate.public_bytes(serialization.Encoding.DER)
        ).hexdigest()
        fingerprint_formatado = ':'.join(
            fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2)
        )

        # Número de série como hex string
        serial_hex = format(serial_number, 'X')

        # Criar registro no banco
        cert_obj = CertificadoDevice.objects.create(
            conta=conta,
            mac_address=mac_address,
            device_id=device_id,
            gateway=gateway,
            csr_pem=csr_pem,
            certificate_pem=cert_pem,
            private_key_pem=None,  # CSR model: chave não sai do dispositivo
            serial_number=serial_hex,
            fingerprint_sha256=fingerprint_formatado,
            expires_at=django_tz.make_aware(
                datetime.fromtimestamp(expira_em.timestamp()),
                timezone=None
            ) if django_tz.is_naive(expira_em) else expira_em,
        )

        logger.info(
            "[CertificadoService] Certificado gerado: device_id=%s serial=%s CN=%s expires=%s",
            device_id,
            serial_hex,
            device_id,
            expira_em.strftime('%Y-%m-%d')
        )

        return cert_obj

    # =========================================================================
    # GERAÇÃO NO SERVIDOR (Legacy / Factory — sem CSR do dispositivo)
    # =========================================================================

    def gerar_certificado_factory(
        self,
        device_id: str,
        mac_address: str,
        conta,
        gateway=None,
        forcar_renovacao: bool = False
    ):
        """
        Gera par chave+certificado no servidor para gravação física na fábrica.

        ⚠️ AVISO: Este método armazena a chave privada no banco de dados.
        Use SOMENTE para provisionamento físico na fábrica (gravação via flash tool).
        Em produção, prefira o fluxo CSR (gerar_certificado_de_csr).

        O arquivo resultante deve ser gravado via esptool.py/NVS partition tool
        e o campo private_key_pem deve ser apagado após a gravação.

        Args:
            device_id (str): ID lógico do dispositivo
            mac_address (str): MAC address do dispositivo
            conta: Instância do modelo Conta
            gateway: Instância do modelo Gateway (opcional)
            forcar_renovacao (bool): Se True, revoga cert existente

        Returns:
            CertificadoDevice: Instância do certificado criado/salvo
        """
        from tds_new.models import CertificadoDevice

        # Verificar cert existente
        if not forcar_renovacao:
            cert_existente = CertificadoDevice.objects.filter(
                conta=conta,
                device_id=device_id,
                is_revoked=False
            ).first()
            if cert_existente:
                raise CertificadoJaExistenteError(
                    f"Dispositivo {device_id} já possui certificado ativo (ID={cert_existente.pk}). "
                    f"Use forcar_renovacao=True para revogar e gerar novo."
                )

        if forcar_renovacao:
            for c in CertificadoDevice.objects.filter(conta=conta, device_id=device_id, is_revoked=False):
                c.revogar(motivo='SUPERSEDED', notas=f'Revogado ao gerar novo certificado (factory) para {device_id}')

        # Gerar chave RSA 2048 no servidor
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        # Gerar certificado auto-assinado pela CA
        serial_number = x509.random_serial_number()
        agora = datetime.now(timezone.utc)
        expira_em = agora + timedelta(days=self.validity_days)

        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, 'BR'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Onkoto IoT'),
            x509.NameAttribute(NameOID.COMMON_NAME, device_id),
        ])

        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.ca_cert.subject)
            .public_key(private_key.public_key())
            .serial_number(serial_number)
            .not_valid_before(agora)
            .not_valid_after(expira_em)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(device_id)]),
                critical=False
            )
            .sign(self.ca_key, hashes.SHA256(), default_backend())
        )

        cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        fingerprint = hashlib.sha256(certificate.public_bytes(serialization.Encoding.DER)).hexdigest()
        fingerprint_formatado = ':'.join(fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2))
        serial_hex = format(serial_number, 'X')

        cert_obj = CertificadoDevice.objects.create(
            conta=conta,
            mac_address=mac_address,
            device_id=device_id,
            gateway=gateway,
            csr_pem=None,
            certificate_pem=cert_pem,
            private_key_pem=private_key_pem,
            serial_number=serial_hex,
            fingerprint_sha256=fingerprint_formatado,
            expires_at=expira_em,
        )

        logger.info(
            "[CertificadoService] Certificado factory gerado: device_id=%s serial=%s MAC=%s",
            device_id, serial_hex, mac_address
        )

        return cert_obj

    # =========================================================================
    # DOWNLOAD — ZIP DE PROVISIONAMENTO
    # =========================================================================

    def gerar_zip_provisionamento(self, certificado) -> bytes:
        """
        Gera o pacote ZIP de provisionamento para gravação no dispositivo.

        Conteúdo do ZIP:
          - ca.crt          → Certificado público da CA (para verificar o broker MQTT)
          - client.crt      → Certificado assinado do dispositivo
          - client.key      → Chave privada RSA (SOMENTE se gerada no servidor — modo factory)
          - README_nvs.txt  → Instruções de gravação na NVS (ESP-IDF)

        Args:
            certificado: Instância de CertificadoDevice

        Returns:
            bytes: Conteúdo do arquivo ZIP
        """
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Certificado da CA
            zf.writestr('ca.crt', self.get_ca_cert_pem())

            # 2. Certificado do dispositivo
            zf.writestr('client.crt', certificado.certificate_pem)

            # 3. Chave privada (SOMENTE se disponível — modo factory)
            if certificado.private_key_pem:
                zf.writestr('client.key', certificado.private_key_pem)
                modo_provisionamento = 'factory (chave gerada no servidor)'
            else:
                modo_provisionamento = 'CSR (chave gerada no dispositivo — não incluída)'

            # 4. README com instruções de gravação NVS
            readme_content = self._gerar_readme_nvs(certificado, modo_provisionamento)
            zf.writestr('README_nvs.txt', readme_content)

        buffer.seek(0)
        return buffer.read()

    def _gerar_readme_nvs(self, certificado, modo_provisionamento: str) -> str:
        """Gera o README com instruções de gravação na NVS do ESP32."""
        device_id = certificado.device_id or certificado.mac_address
        has_key = bool(certificado.private_key_pem)

        instrucoes = f"""
=======================================================================
  PROVISIONAMENTO DE CERTIFICADO X.509 — DISPOSITIVO IoT (ESP-IDF/NVS)
=======================================================================
Device ID    : {device_id}
MAC Address  : {certificado.mac_address}
Serial Cert  : {certificado.serial_number}
Fingerprint  : {certificado.fingerprint_sha256 or 'N/A'}
Modo         : {modo_provisionamento}
Gerado em    : {certificado.issued_at.strftime('%Y-%m-%d %H:%M:%S UTC') if certificado.issued_at else 'N/A'}
Expira em    : {certificado.expires_at.strftime('%Y-%m-%d') if certificado.expires_at else 'N/A'}
=======================================================================

ARQUIVOS NESTE PACOTE:
  ca.crt      → Certificado raiz da CA (gravar na NVS partition 'certs')
  client.crt  → Certificado assinado do dispositivo (gravar na NVS partition 'certs')
{  "  client.key  → Chave privada RSA 2048 (gravar na NVS partition 'certs')" if has_key else "  [client.key NÃO incluso — chave permanece no dispositivo (modo CSR)]" }

=======================================================================
GRAVAÇÃO VIA ESP-IDF NVS PARTITION TOOL
=======================================================================

1. Criar CSV de certificados (certs.csv):

   key,type,encoding,value
   ns_certs,namespace,,
   ca_crt,data,file,ca.crt
   client_crt,data,file,client.crt
{  "   client_key,data,file,client.key" if has_key else "   # client_key: já gravada no dispositivo (modo CSR)" }

2. Gerar imagem NVS:

   python $IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py \\
       generate certs.csv certs.bin 0x6000

3. Gravar imagem NVS na partição 'certs':

   esptool.py --port /dev/ttyUSB0 write_flash 0x3FC000 certs.bin
   # Ajuste o offset conforme o partition table do firmware (ver partition_table.csv)

=======================================================================
CÓDIGO FIRMWARE (LEITURA VIA NVS — ESP-IDF)
=======================================================================

   static const char* CERT_NAMESPACE = "ns_certs";

   // Leitura do ca.crt
   nvs_handle_t handle;
   nvs_open_from_partition("certs", CERT_NAMESPACE, NVS_READONLY, &handle);
   size_t ca_size = 0;
   nvs_get_str(handle, "ca_crt", NULL, &ca_size);
   char* ca_pem = malloc(ca_size);
   nvs_get_str(handle, "ca_crt", ca_pem, &ca_size);

   // Idem para "client_crt" e "client_key"

=======================================================================
MQTT BROKER — CONFIGURAÇÃO mTLS
=======================================================================
   Host         : <configurado no firmware via NVS 'setup'>
   Port         : 8883 (TLS/mTLS)
   Client ID    : {device_id}
   Topic        : telemetry/{device_id}-<LAST4HEX_MAC>/data
   CA           : ca.crt
   Client Cert  : client.crt
   Client Key   : client.key (no dispositivo)

=======================================================================
FIM DAS INSTRUÇÕES
=======================================================================
"""
        return instrucoes.strip()

    # =========================================================================
    # REVOGAÇÃO
    # =========================================================================

    def revogar_certificado(self, certificado, motivo: str, notas: str = '', usuario=None):
        """
        Revoga um certificado X.509 e registra o evento.

        Args:
            certificado: Instância de CertificadoDevice
            motivo (str): Código do motivo (REVOKE_REASON_CHOICES)
            notas (str): Observações adicionais
            usuario: Usuário que realizou a revogação (para auditoria)

        Returns:
            CertificadoDevice: Instância atualizada
        """
        if certificado.is_revoked:
            raise CertificadoServiceError(
                f"Certificado ID={certificado.pk} já está revogado."
            )

        notas_completas = notas
        if usuario:
            notas_completas = f"[{usuario.email}] {notas}"

        certificado.revogar(motivo=motivo, notas=notas_completas)

        logger.info(
            "[CertificadoService] Certificado revogado: ID=%s device_id=%s motivo=%s usuario=%s",
            certificado.pk,
            certificado.device_id or certificado.mac_address,
            motivo,
            getattr(usuario, 'email', 'sistema')
        )

        return certificado

    # =========================================================================
    # BOOTSTRAP CERTIFICATE — cert compartilhado gravado na fábrica
    # =========================================================================

    def gerar_bootstrap_cert(self, label: str, criado_por=None):
        """
        Gera um novo Bootstrap Certificate para gravação em lote na fábrica.

        O bootstrap cert é COMPARTILHADO — todos os devices de um lote saem de
        fábrica com o mesmo par (bootstrap.crt + bootstrap.key).

        Ele só autoriza conexão ao tópico de provisionamento no broker.
        A chave privada é armazenada no banco para download pelo admin.

        Args:
            label (str): Identificação do lote (ex: 'Produção Q1-2026')
            criado_por: Usuário admin que está gerando

        Returns:
            BootstrapCertificate: Instância gerada e persistida
        """
        from tds_new.models import BootstrapCertificate

        # Desativar bootstrap cert anterior (se houver)
        anteriores_ativos = BootstrapCertificate.objects.filter(
            is_active=True, is_revoked=False
        )
        for b in anteriores_ativos:
            b.desativar()
            logger.info(
                "[CertificadoService] Bootstrap cert anterior desativado: ID=%s label='%s'",
                b.pk, b.label
            )

        # Gerar chave RSA 2048
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        # Gerar certificado assinado pela CA
        serial_number = x509.random_serial_number()
        agora = datetime.now(timezone.utc)
        expira_em = agora + timedelta(days=self.validity_days)

        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, 'BR'),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Onkoto IoT'),
            x509.NameAttribute(NameOID.COMMON_NAME, f'bootstrap-{label[:40]}'),
        ])

        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.ca_cert.subject)
            .public_key(private_key.public_key())
            .serial_number(serial_number)
            .not_valid_before(agora)
            .not_valid_after(expira_em)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
            # SAN com indicação de bootstrap para fácil identificação
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName('bootstrap.onkoto.iot')]),
                critical=False
            )
            .sign(self.ca_key, hashes.SHA256(), default_backend())
        )

        cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8')
        fingerprint = hashlib.sha256(certificate.public_bytes(serialization.Encoding.DER)).hexdigest()
        fingerprint_formatado = ':'.join(fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2))
        serial_hex = format(serial_number, 'X')

        bootstrap = BootstrapCertificate(
            label=label,
            certificate_pem=cert_pem,
            private_key_pem=private_key_pem,
            serial_number=serial_hex,
            fingerprint_sha256=fingerprint_formatado,
            expires_at=expira_em,
            is_active=True,
            created_by=criado_por,
        )
        bootstrap.save()

        logger.info(
            "[CertificadoService] Bootstrap cert gerado: ID=%s label='%s' serial=%s",
            bootstrap.pk, label, serial_hex
        )

        return bootstrap

    def gerar_zip_bootstrap(self, bootstrap) -> bytes:
        """
        Gera ZIP para download pelo operador de fábrica.

        Conteúdo:
          bootstrap.crt  → Certificado bootstrap (gravado em TODOS os devices)
          bootstrap.key  → Chave privada bootstrap (gravada em TODOS os devices)
          ca.crt         → Certificado raiz da CA
          README_nvs.txt → Instruções de gravação via NVS partition tool

        Raises:
            CertificadoServiceError: Se a chave privada já foi removida (download já realizado).
        """
        if not bootstrap.private_key_pem:
            raise CertificadoServiceError(
                f"Bootstrap cert ID={bootstrap.pk} '{bootstrap.label}': "
                "a chave privada já foi removida do banco após o primeiro download (medida de segurança). "
                "Para gerar um novo pacote de fábrica, gere um novo Bootstrap Certificate."
            )
        ca_pem = self.get_ca_cert_pem()

        instrucoes = f"""
=======================================================================
BOOTSTRAP CERTIFICATE — PACOTE DE FÁBRICA
Label    : {bootstrap.label}
Serial   : {bootstrap.serial_number}
Valid    : até {bootstrap.expires_at.strftime('%d/%m/%Y')}
=======================================================================

AVISO: Este pacote é COMPARTILHADO — grave nos TODOS os devices do lote.
Não compartilhe fora da equipe de fábrica.

GRAVAÇÃO NVS (ESP-IDF):
  Namespace da partição: 'bootstrap'

  nvs_set_str(handle, "cert",    <conteúdo de bootstrap.crt>);
  nvs_set_str(handle, "key",     <conteúdo de bootstrap.key>);
  nvs_set_str(handle, "ca_crt",  <conteúdo de ca.crt>);

  Ou via nvs_partition_tool:
    python nvs_partition_gen.py --input bootstrap_nvs.csv \\
           --output bootstrap_nvs.bin --size 0x6000

PARTIÇÃO DO DISPOSITIVO:
  Firmware lê bootstrap cert de NVS 'bootstrap' e o usa SOMENTE para
  o pedido de auto-registro (POST /api/provision/register/).
  Após receber o cert individual, passa a usar a partição 'certs'.

APÓS PROVISIONAMENTO:
  O device receberá um certificado individual assinado pela CA.
  O bootstrap cert continua armazenado, mas o firmware prioriza o cert
  individual se disponível.
""".strip()

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('bootstrap.crt', bootstrap.certificate_pem)
            zf.writestr('bootstrap.key', bootstrap.private_key_pem)
            zf.writestr('ca.crt', ca_pem)
            zf.writestr('README_nvs.txt', instrucoes)
        return buf.getvalue()

    def revogar_bootstrap_cert(self, bootstrap, motivo: str, notas: str = '', usuario=None):
        """
        Revoga um Bootstrap Certificate.

        ⚠️ ATENÇÃO: Revogar o bootstrap cert IMPEDE que devices ainda não
        provisionados se conectem ao broker. Use apenas em caso de comprometimento
        da chave privada. Para rotação planejada, gere um novo sem revogar o anterior.

        Args:
            bootstrap: Instância de BootstrapCertificate
            motivo (str): Código do motivo (REVOKE_REASON_CHOICES)
            notas (str): Observações adicionais
            usuario: Usuário admin que executou

        Returns:
            BootstrapCertificate: Instância atualizada
        """
        if bootstrap.is_revoked:
            raise CertificadoServiceError(
                f"Bootstrap cert ID={bootstrap.pk} já está revogado."
            )

        notas_completas = notas
        if usuario:
            notas_completas = f"[{getattr(usuario, 'email', str(usuario))}] {notas}"

        bootstrap.revogar(motivo=motivo, notas=notas_completas, usuario=usuario)

        logger.warning(
            "[CertificadoService] BOOTSTRAP CERT REVOGADO: ID=%s label='%s' motivo=%s usuario=%s",
            bootstrap.pk, bootstrap.label, motivo,
            getattr(usuario, 'email', 'sistema')
        )

        return bootstrap

    # =========================================================================
    # AUTO-REGISTRO — processamento do pedido do device no primeiro boot
    # =========================================================================

    def processar_auto_registro(
        self,
        mac_address: str,
        serial_number_device: str = '',
        modelo: str = '',
        fw_version: str = '',
        ip_origem: str = None,
        bootstrap_fingerprint: str = None,
        csr_pem: str = '',
    ):
        """
        Processa o pedido de auto-registro enviado pelo device no primeiro boot.

        Chamado pela API REST POST /api/provision/register/ quando o device conecta
        usando o bootstrap cert e reporta sua identidade.

        Comportamento:
          - Device já em estado PENDENTE ou PROVISIONADO: retorna registro existente
          - Device novo: cria RegistroProvisionamento com status=PENDENTE

        Args:
            mac_address (str): MAC address do device
            serial_number_device (str): Serial do hardware
            modelo (str): Modelo do device (ex: DCU-8210)
            fw_version (str): Versão do firmware
            ip_origem (str): IP da requisição
            bootstrap_fingerprint (str): Fingerprint SHA-256 do bootstrap cert usado
            csr_pem (str): CSR PKCS#10 enviado pelo device (firmware atualizado).
                           Quando presente, persiste no RegistroProvisionamento para
                           uso pelo admin ao gerar o cert individual via fluxo CSR.

        Returns:
            tuple: (RegistroProvisionamento, criado: bool)
            criado=True se este é o primeiro registro, False se já existia
        """
        from tds_new.models import RegistroProvisionamento, BootstrapCertificate

        # Verificar se já existe registro não rejeitado para este MAC
        registro_existente = RegistroProvisionamento.objects.filter(
            mac_address=mac_address
        ).exclude(status='REJEITADO').order_by('-created_at').first()

        if registro_existente:
            logger.info(
                "[CertificadoService] Auto-registro: MAC %s já possui registro ID=%s status=%s",
                mac_address, registro_existente.pk, registro_existente.status
            )
            return registro_existente, False

        # Identificar bootstrap cert utilizado pela fingerprint (se informada)
        bootstrap_cert_obj = None
        if bootstrap_fingerprint:
            bootstrap_cert_obj = BootstrapCertificate.objects.filter(
                fingerprint_sha256=bootstrap_fingerprint
            ).first()

        # Criar registro de provisionamento
        registro = RegistroProvisionamento.objects.create(
            mac_address=mac_address,
            serial_number_device=serial_number_device or None,
            modelo=modelo or None,
            fw_version=fw_version or None,
            ip_origem=ip_origem or None,
            bootstrap_cert=bootstrap_cert_obj,
            csr_pem=csr_pem or None,
            status='PENDENTE',
        )

        logger.info(
            "[CertificadoService] Auto-registro criado: ID=%s MAC=%s modelo=%s fw=%s",
            registro.pk, mac_address, modelo, fw_version
        )

        return registro, True

