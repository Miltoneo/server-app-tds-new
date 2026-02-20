"""
Gestão de CRL (Certificate Revocation List) — TDS New

Gera e publica a CRL que o Mosquitto broker usa para bloquear conexões
de dispositivos cujos certificados foram revogados.

Fluxo:
  1. model.revogar() é chamado por uma view admin
  2. model.revogar() chama atualizar_crl_broker()
  3. atualizar_crl_broker() → gerar_crl_pem() → escreve em settings.MQTT_CRL_PATH
  4. Mosquitto relê o arquivo CRL a cada nova conexão TLS (sem necessidade de restart)

Dependências em settings.py:
  MQTT_CA_CERT_PATH      → certificado público da CA (ca.crt)
  MQTT_CA_KEY_PATH       → chave privada da CA (ca.key)
  MQTT_CA_KEY_PASSWORD   → senha da chave (vazio se sem senha)
  MQTT_CRL_PATH          → caminho de saída da CRL (ex: /etc/mosquitto/certs/ca.crl)

Comportamento em caso de erro:
  atualizar_crl_broker() NÃO propaga exceções — a revogação no banco já foi
  efetuada e não deve ser desfeita por falha de infra. O erro é logado e a CRL
  pode ser regenerada manualmente via chamada direta a gerar_crl_pem().
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento: choices do modelo → ReasonFlags da cryptography
# ---------------------------------------------------------------------------
# None = não inclui extensão CRLReason (RFC 5280 §5.3.1 — omitir = unspecified)
_REASON_MAP = {
    'COMPROMISED': x509.ReasonFlags.key_compromise,
    'KEY_COMPROMISE': x509.ReasonFlags.key_compromise,
    'SUPERSEDED': x509.ReasonFlags.superseded,
    'ROTATION': x509.ReasonFlags.superseded,
    'CESSATION': x509.ReasonFlags.cessation_of_operation,
    'AFFILIATION_CHANGED': x509.ReasonFlags.affiliation_changed,
    'OTHER': None,
}


def gerar_crl_pem() -> str:
    """
    Gera a CRL completa em formato PEM incluindo todos os certificados
    revogados de CertificadoDevice e BootstrapCertificate.

    Returns:
        str: CRL em formato PEM assinada pela CA

    Raises:
        FileNotFoundError: Se os arquivos de CA não existirem
        Exception: Para outros erros de criptografia
    """
    # Import tardio para evitar circular import (models importa utils)
    from tds_new.models.certificados import BootstrapCertificate, CertificadoDevice

    # --- Carregar CA ---
    ca_cert_path = Path(settings.MQTT_CA_CERT_PATH)
    ca_key_path = Path(settings.MQTT_CA_KEY_PATH)
    ca_key_password = getattr(settings, 'MQTT_CA_KEY_PASSWORD', '') or None

    if not ca_cert_path.exists():
        raise FileNotFoundError(
            f"Certificado da CA não encontrado: {ca_cert_path}. "
            "Verifique settings.MQTT_CA_CERT_PATH."
        )
    if not ca_key_path.exists():
        raise FileNotFoundError(
            f"Chave privada da CA não encontrada: {ca_key_path}. "
            "Verifique settings.MQTT_CA_KEY_PATH."
        )

    with open(ca_cert_path, 'rb') as f:
        ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())

    password_bytes = ca_key_password.encode('utf-8') if ca_key_password else None
    with open(ca_key_path, 'rb') as f:
        ca_key = serialization.load_pem_private_key(
            f.read(), password=password_bytes, backend=default_backend()
        )

    # --- Coletar todos os certificados revogados ---
    agora = datetime.now(timezone.utc)

    revogados_device = list(
        CertificadoDevice.objects
        .filter(is_revoked=True)
        .values('serial_number', 'revoked_at', 'revoke_reason')
        .order_by('revoked_at')
    )

    revogados_bootstrap = list(
        BootstrapCertificate.objects
        .filter(is_revoked=True)
        .values('serial_number', 'revoked_at', 'revoke_reason')
        .order_by('revoked_at')
    )

    todos_revogados = revogados_device + revogados_bootstrap

    # --- Construir CRL ---
    # next_update: 7 dias (Mosquitto verifica a data; CRL expirada = todos os certs bloqueados)
    next_update = agora + timedelta(days=7)

    builder = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca_cert.subject)
        .last_update(agora)
        .next_update(next_update)
    )

    for entry in todos_revogados:
        try:
            serial_int = int(entry['serial_number'], 16)
        except (ValueError, TypeError):
            logger.warning(
                "[CRL] Serial inválido ignorado (não é hex): %r", entry['serial_number']
            )
            continue

        revoked_at = entry.get('revoked_at') or agora
        if revoked_at.tzinfo is None:
            revoked_at = revoked_at.replace(tzinfo=timezone.utc)

        revoked_builder = (
            x509.RevokedCertificateBuilder()
            .serial_number(serial_int)
            .revocation_date(revoked_at)
        )

        reason_flag = _REASON_MAP.get(entry.get('revoke_reason'), None)
        if reason_flag is not None:
            revoked_builder = revoked_builder.add_extension(
                x509.CRLReason(reason_flag),
                critical=False,
            )

        builder = builder.add_revoked_certificate(
            revoked_builder.build(default_backend())
        )

    crl = builder.sign(
        private_key=ca_key,
        algorithm=hashes.SHA256(),
        backend=default_backend(),
    )

    return crl.public_bytes(serialization.Encoding.PEM).decode('utf-8')


def atualizar_crl_broker() -> None:
    """
    Gera a CRL e escreve no arquivo configurado em settings.MQTT_CRL_PATH.

    O Mosquitto relê o arquivo CRL a cada nova conexão TLS (não requer restart
    desde que `crlfile` esteja configurado no mosquitto.conf).

    Em caso de erro, loga o problema mas NÃO lança exceção — a revogação no
    banco já foi efetuada e não deve ser desfeita por falha de infra. Use
    gerar_crl_pem() diretamente para regenerar a CRL manualmente.
    """
    crl_path_str = getattr(settings, 'MQTT_CRL_PATH', '')
    if not crl_path_str:
        logger.error(
            "[CRL] settings.MQTT_CRL_PATH não configurado — CRL não atualizada. "
            "Configure o caminho do arquivo CRL para o broker Mosquitto."
        )
        return

    crl_path = Path(crl_path_str)

    try:
        crl_pem = gerar_crl_pem()

        # Garante que o diretório de destino existe
        crl_path.parent.mkdir(parents=True, exist_ok=True)

        crl_path.write_text(crl_pem, encoding='utf-8')

        # Parse para obter contagem de entradas e next_update para o log
        crl_obj = x509.load_pem_x509_crl(crl_pem.encode(), default_backend())
        n = sum(1 for _ in crl_obj)
        next_update = crl_obj.next_update_utc if hasattr(crl_obj, 'next_update_utc') else crl_obj.next_update

        logger.info(
            "[CRL] Arquivo atualizado: %s | %d entrada(s) revogada(s) | válida até %s",
            crl_path,
            n,
            next_update.strftime('%d/%m/%Y %H:%M UTC') if next_update else 'N/A',
        )

    except FileNotFoundError as e:
        logger.error(
            "[CRL] Arquivos da CA não encontrados — CRL não atualizada. "
            "Verifique MQTT_CA_CERT_PATH e MQTT_CA_KEY_PATH: %s", e
        )
    except Exception as e:
        logger.exception("[CRL] Erro inesperado ao atualizar CRL: %s", e)
