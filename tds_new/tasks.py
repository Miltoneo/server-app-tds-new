"""
Tasks Celery — TDS New

Tasks periódicas para gestão do ciclo de vida de certificados X.509.

Schedulers registrados em settings.CELERY_BEAT_SCHEDULE:
  agendar_renovacoes          → diário às 02:00 UTC
  alertar_renovacoes_pendentes → a cada hora

Nota OTA:
  A renovação efetiva do certificado requer que o firmware ESP32 solicite
  o novo cert via OTA. As tasks aqui implementam o lado servidor:
  - Identificar certs que entram na janela de renovação (2 anos antes do vencimento)
  - Agendar via model.agendar_renovacao()
  - Alertar os admins quando a data de renovação chega
  A entrega do novo cert via OTA é responsabilidade do consumer MQTT (fase futura).
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='tds_new.agendar_renovacoes')
def agendar_renovacoes_task(self):
    """
    Identifica certificados que entram na janela de renovação OTA e os agenda.

    Critérios para agendamento:
      - Certificado ATIVO (is_revoked=False)
      - Ainda não agendado (renewal_scheduled=False)
      - Expira em até 730 dias (2 anos — janela de renovação antecipada)

    Scheduled: diariamente às 02:00 UTC (ver settings.CELERY_BEAT_SCHEDULE)
    """
    from tds_new.models import CertificadoDevice  # import tardio — evita load prematuro

    limite = timezone.now() + timedelta(days=730)

    candidatos = CertificadoDevice.objects.filter(
        is_revoked=False,
        renewal_scheduled=False,
        expires_at__lte=limite,
    )

    total = candidatos.count()
    agendados = 0
    erros = 0

    for cert in candidatos.iterator():
        try:
            if cert.agendar_renovacao():
                agendados += 1
        except Exception as exc:
            erros += 1
            logger.error(
                "[Task:agendar_renovacoes] Erro ao agendar cert ID=%s MAC=%s: %s",
                cert.pk, cert.mac_address, exc,
            )

    logger.info(
        "[Task:agendar_renovacoes] Concluído: %d candidatos | %d agendados | %d erros",
        total, agendados, erros,
    )
    return {'candidatos': total, 'agendados': agendados, 'erros': erros}


@shared_task(bind=True, name='tds_new.alertar_renovacoes_pendentes')
def alertar_renovacoes_pendentes_task(self):
    """
    Identifica certificados com renovação OTA vencida e emite alerta para admin.

    Critérios:
      - renewal_scheduled=True (agendado pela task anterior)
      - renewal_date <= agora (data de início da janela de renovação já passou)
      - Certificado ainda ativo (is_revoked=False)

    Scheduled: a cada hora (ver settings.CELERY_BEAT_SCHEDULE)

    Nota:
      Esta task apenas loga o alerta. A entrega do novo cert ao device
      via MQTT OTA será implementada quando o firmware suportar o fluxo
      de renovação (fase futura). O alerta permite ação manual pelos admins.
    """
    from tds_new.models import CertificadoDevice

    agora = timezone.now()

    pendentes = CertificadoDevice.objects.filter(
        is_revoked=False,
        renewal_scheduled=True,
        renewal_date__lte=agora,
    ).select_related('gateway', 'conta')

    total = pendentes.count()

    if total == 0:
        logger.debug("[Task:alertar_renovacoes] Nenhuma renovação pendente.")
        return {'pendentes': 0}

    logger.warning(
        "[Task:alertar_renovacoes] %d certificado(s) com renovação OTA vencida:",
        total,
    )

    for cert in pendentes.iterator():
        dias_ate_expiracao = cert.dias_para_expiracao
        logger.warning(
            "  → ID=%s | MAC=%s | device_id=%s | expira em %d dias | "
            "renovação deveria ter iniciado em %s",
            cert.pk,
            cert.mac_address,
            cert.device_id or 'N/A',
            dias_ate_expiracao,
            cert.renewal_date.strftime('%d/%m/%Y') if cert.renewal_date else 'N/A',
        )

    logger.warning(
        "[Task:alertar_renovacoes] Ação necessária: inicie o processo de renovação OTA "
        "para os %d device(s) listados acima.",
        total,
    )

    return {'pendentes': total}
