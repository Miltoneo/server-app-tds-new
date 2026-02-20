"""
API REST de Provisionamento — TDS New

Endpoint chamado pelo device no primeiro boot usando o bootstrap cert.
Permite que o device reporte sua identidade e seja registrado no sistema.

Autenticação:
  mTLS ao nível do nginx/broker (o bootstrap cert é validado pelo proxy reverso).
  Esta view assume que a requisição já passou pela camada TLS.
"""

import json
import logging
import re

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


def _mac_valido(mac: str) -> bool:
    """Valida formato MAC address: aa:bb:cc:dd:ee:ff"""
    return bool(re.match(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$', mac))


def _check_rate_limit(ip: str) -> bool:
    """
    Verifica se o IP excedeu o limite de requisições ao endpoint de auto-registro.

    Usa o cache Django (Redis ou DB, conforme settings.CACHES) com janela deslizante
    simples baseada em TTL.

    Returns:
        True  → limite excedido, requisição deve ser bloqueada (HTTP 429)
        False → dentro do limite, requisição pode prosseguir
    """
    max_requests = getattr(settings, 'PROVISION_RATE_LIMIT_MAX', 10)
    window = getattr(settings, 'PROVISION_RATE_LIMIT_WINDOW', 3600)

    cache_key = f"autoregister_rl:{ip}"

    try:
        count = cache.get(cache_key, 0)
        if count >= max_requests:
            return True  # Bloquear antes de incrementar
        if count == 0:
            # Primeira requisição nesta janela — inicializa com TTL
            cache.set(cache_key, 1, window)
        else:
            cache.incr(cache_key)
    except Exception:
        # Se o cache estiver indisponível, permitir (fail-open)
        # para não bloquear devices legítimos por falha de infraestrutura
        pass

    return False  # Permitir


@csrf_exempt
@require_http_methods(['POST'])
def auto_register_view(request):
    """
    Endpoint de auto-registro chamado pelo device no primeiro boot.

    O device (usando o bootstrap cert para mTLS) envia sua identidade.
    O backend registra o device como PENDENTE para revisão pelo admin.

    Request Body (JSON):
        {
            "mac":        "aa:bb:cc:dd:ee:ff",  // obrigatório
            "serial":     "DCU-8210-001234",     // opcional
            "modelo":     "DCU-8210",            // opcional
            "fw_version": "4.0.1",               // opcional
            "bootstrap_fingerprint": "AA:BB:..."  // opcional — fingerprint do bootstrap cert usado
        }

    Responses:
        200 registered (novo registro criado)
        200 already_registered (device já havia se registrado antes)
        400 invalid_request (MAC ausente ou inválido)
        429 rate_limited (muitas tentativas do mesmo IP)
        500 server_error

    Nota de Segurança:
        Esta view não autentica com usuário/senha Django. A autenticação
        é feita no nível de mTLS (nginx/broker valida que o client cert
        foi assinado pela CA). Ao nível da view, qualquer requisição que
        chegue aqui já passou pela validação do bootstrap cert.
    """
    from tds_new.services.certificados import CertificadoService, CertificadoServiceError

    # Capturar IP de origem (necessário para rate limiting, antes de qualquer lógica)
    ip_origem = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR', '0.0.0.0')
    )

    # Rate limiting por IP
    if _check_rate_limit(ip_origem):
        logger.warning("[AutoRegister] Rate limit excedido: IP=%s", ip_origem)
        return JsonResponse(
            {
                'status': 'error',
                'code': 'rate_limited',
                'message': 'Muitas tentativas de registro. Tente novamente mais tarde.',
            },
            status=429
        )

    # Parsear body JSON
    try:
        body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {'status': 'error', 'code': 'invalid_request', 'message': 'Body deve ser JSON válido'},
            status=400
        )

    mac = body.get('mac', '').strip().lower()

    # Validar MAC
    if not mac:
        return JsonResponse(
            {'status': 'error', 'code': 'invalid_request', 'message': 'Campo "mac" é obrigatório'},
            status=400
        )
    if not _mac_valido(mac):
        return JsonResponse(
            {'status': 'error', 'code': 'invalid_request', 'message': 'MAC address inválido (formato: aa:bb:cc:dd:ee:ff)'},
            status=400
        )

    try:
        service = CertificadoService()
        registro, criado = service.processar_auto_registro(
            mac_address=mac,
            serial_number_device=body.get('serial', ''),
            modelo=body.get('modelo', ''),
            fw_version=body.get('fw_version', ''),
            ip_origem=ip_origem,
            bootstrap_fingerprint=body.get('bootstrap_fingerprint', ''),
            csr_pem=body.get('csr_pem', ''),
        )

        if criado:
            logger.info(
                "[AutoRegister] Novo device: MAC=%s modelo=%s fw=%s IP=%s",
                mac, body.get('modelo'), body.get('fw_version'), ip_origem
            )
            return JsonResponse({
                'status': 'ok',
                'code': 'registered',
                'message': 'Device registrado. Aguardando alocação pelo administrador.',
                'registro_id': registro.pk,
            })
        else:
            logger.info(
                "[AutoRegister] Device já registrado: MAC=%s status=%s",
                mac, registro.status
            )
            response_data = {
                'status': 'ok',
                'code': 'already_registered',
                'message': f'Device já registrado. Status: {registro.get_status_display()}',
                'registro_status': registro.status,
                'registro_id': registro.pk,
            }
            # Se já provisionado, indicar que o device deve usar o cert individual
            if registro.status == 'PROVISIONADO':
                response_data['message'] = (
                    'Device já provisionado. Use o certificado individual gravado no device.'
                )
            return JsonResponse(response_data)

    except CertificadoServiceError as e:
        logger.error("[AutoRegister] Erro: %s", e)
        return JsonResponse(
            {'status': 'error', 'code': 'server_error', 'message': str(e)},
            status=500
        )
    except Exception as e:
        logger.exception("[AutoRegister] Erro inesperado: %s", e)
        return JsonResponse(
            {'status': 'error', 'code': 'server_error', 'message': 'Erro interno'},
            status=500
        )
