## backend/app/services/retention_service.py
"""
Política de retenção de dados.

Mantém a plataforma leve e performática apagando periodicamente:
- Posições de GPS mais antigas que `POSITION_RETENTION_DAYS`.
- Eventos operacionais (events, alerts, geofence_events) mais antigos
  que `EVENT_RETENTION_DAYS`.

NUNCA apaga: técnicos, dispositivos, usuários, geofences (configuração)
ou qualquer outra tabela de cadastro/configuração.

A limpeza roda em lotes (batches) para evitar prender o banco de dados
com um único DELETE gigante (locks longos, bloqueio de outras queries,
uso excessivo de memória). Cada lote é apagado e commitado
separadamente antes de seguir para o próximo.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Type

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.position import Position
from app.models.event import Event
from app.models.alert import Alert
from app.models.geofence_event import GeofenceEvent

logger = logging.getLogger(__name__)


async def _delete_in_batches(
    session: AsyncSession,
    model: Type,
    timestamp_column,
    cutoff: datetime,
    batch_size: int,
) -> int:
    """
    Apaga registros de `model` com `timestamp_column` anterior a `cutoff`,
    em lotes de `batch_size`, commitando a cada lote.

    Estratégia: seleciona um lote de IDs mais antigos que o cutoff e apaga
    apenas esses IDs. Repete até não sobrar nenhum registro expirado.
    Isso evita um único DELETE longo que prenderia a tabela inteira.
    """
    total_deleted = 0

    while True:
        # Seleciona um lote de IDs expirados (sem trazer a linha inteira)
        select_stmt = (
            select(model.id)
            .where(timestamp_column < cutoff)
            .limit(batch_size)
        )
        result = await session.execute(select_stmt)
        ids = [row[0] for row in result.all()]

        if not ids:
            break

        delete_stmt = delete(model).where(model.id.in_(ids))
        await session.execute(delete_stmt)
        await session.commit()

        total_deleted += len(ids)

        # Se o lote veio menor que o batch_size, não há mais registros expirados
        if len(ids) < batch_size:
            break

    return total_deleted


async def run_retention_cleanup(batch_size: Optional[int] = None) -> dict:
    """
    Executa uma rodada completa de limpeza de retenção e retorna um
    resumo com a quantidade de registros removidos por tabela.

    Pode ser chamada manualmente (ex: script, endpoint admin, teste)
    ou automaticamente pelo agendador em `start_periodic_retention_cleanup`.
    """
    settings = get_settings()
    batch_size = batch_size or settings.retention_cleanup_batch_size

    now = datetime.utcnow()
    position_cutoff = now - timedelta(days=settings.position_retention_days)
    event_cutoff = now - timedelta(days=settings.event_retention_days)

    logger.info(
        "Iniciando limpeza de retenção | positions < %s (retention=%sd) | "
        "events/alerts/geofence_events < %s (retention=%sd) | batch_size=%s",
        position_cutoff.isoformat(),
        settings.position_retention_days,
        event_cutoff.isoformat(),
        settings.event_retention_days,
        batch_size,
    )

    summary = {
        "positions": 0,
        "events": 0,
        "alerts": 0,
        "geofence_events": 0,
    }

    async with AsyncSessionLocal() as session:
        try:
            summary["positions"] = await _delete_in_batches(
                session, Position, Position.timestamp, position_cutoff, batch_size
            )
            summary["events"] = await _delete_in_batches(
                session, Event, Event.event_timestamp, event_cutoff, batch_size
            )
            summary["alerts"] = await _delete_in_batches(
                session, Alert, Alert.triggered_at, event_cutoff, batch_size
            )
            summary["geofence_events"] = await _delete_in_batches(
                session, GeofenceEvent, GeofenceEvent.timestamp, event_cutoff, batch_size
            )
        except Exception:
            logger.exception("Erro durante a limpeza de retenção de dados - rollback do lote atual")
            raise
        finally:
            await session.close()

    total = sum(summary.values())
    logger.info(
        "✅ Limpeza de retenção concluída | positions=%s | events=%s | alerts=%s | "
        "geofence_events=%s | total=%s registros removidos",
        summary["positions"],
        summary["events"],
        summary["alerts"],
        summary["geofence_events"],
        total,
    )

    return summary


async def start_periodic_retention_cleanup(interval_seconds: Optional[int] = None) -> None:
    """
    Loop em background que roda `run_retention_cleanup` periodicamente
    (padrão: a cada 24h, configurável via RETENTION_CLEANUP_INTERVAL_HOURS).

    Segue o mesmo padrão das demais tarefas periódicas da aplicação
    (sincronização de posições e verificação de geofences em app/main.py).
    """
    settings = get_settings()

    if not settings.retention_cleanup_enabled:
        logger.warning("Limpeza automática de retenção está DESABILITADA (RETENTION_CLEANUP_ENABLED=false)")
        return

    interval_seconds = interval_seconds or (settings.retention_cleanup_interval_hours * 3600)

    logger.info(
        "Agendador de retenção de dados iniciado | intervalo=%sh | position_retention=%sd | event_retention=%sd",
        interval_seconds / 3600,
        settings.position_retention_days,
        settings.event_retention_days,
    )

    while True:
        try:
            await run_retention_cleanup()
        except Exception as exc:
            # Nunca deixa a exceção matar a task em background;
            # apenas loga e tenta novamente no próximo ciclo.
            logger.error("Falha na execução periódica da limpeza de retenção: %s", exc)

        await asyncio.sleep(interval_seconds)
