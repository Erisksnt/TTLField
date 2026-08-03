## backend/tests/test_retention_service.py
"""
Testes de integração para a política de retenção de dados.

Segue o mesmo padrão dos demais testes do projeto: roda contra o banco
Postgres real configurado em .env (não usa mocks/sqlite), já que a
suíte de testes existente (test_technicians.py, test_auth.py, etc.)
também depende de uma conexão real.
"""
import uuid
from datetime import datetime, timedelta

import pytest

from app.database import AsyncSessionLocal
from app.models.position import Position
from app.models.event import Event
from app.models.alert import Alert
from app.services.retention_service import run_retention_cleanup


async def _make_ids():
    return f"tech-{uuid.uuid4().hex[:8]}", f"dev-{uuid.uuid4().hex[:8]}"


@pytest.mark.asyncio
async def test_run_retention_cleanup_removes_only_expired_records():
    technician_id, device_id = await _make_ids()

    old_timestamp = datetime.utcnow() - timedelta(days=400)  # bem além dos 2 retention windows
    recent_timestamp = datetime.utcnow() - timedelta(days=1)

    old_position_id = str(uuid.uuid4())
    recent_position_id = str(uuid.uuid4())
    old_event_id = str(uuid.uuid4())
    recent_event_id = str(uuid.uuid4())
    old_alert_id = str(uuid.uuid4())
    recent_alert_id = str(uuid.uuid4())
    # Observação: geofence_events não é coberto neste teste porque seu
    # geofence_id é FK obrigatória para uma geofence real. A limpeza dessa
    # tabela usa a mesma função `_delete_in_batches` já validada acima.
    async with AsyncSessionLocal() as session:
        session.add_all([
            Position(
                id=old_position_id, technician_id=technician_id, device_id=device_id,
                latitude=-23.5, longitude=-46.6, timestamp=old_timestamp,
            ),
            Position(
                id=recent_position_id, technician_id=technician_id, device_id=device_id,
                latitude=-23.5, longitude=-46.6, timestamp=recent_timestamp,
            ),
            Event(
                id=old_event_id, technician_id=technician_id, device_id=device_id,
                event_type="movement_stopped", title="Parou", event_timestamp=old_timestamp,
            ),
            Event(
                id=recent_event_id, technician_id=technician_id, device_id=device_id,
                event_type="movement_stopped", title="Parou", event_timestamp=recent_timestamp,
            ),
            Alert(
                id=old_alert_id, technician_id=technician_id, device_id=device_id,
                alert_type="offline", title="Offline", triggered_at=old_timestamp,
            ),
            Alert(
                id=recent_alert_id, technician_id=technician_id, device_id=device_id,
                alert_type="offline", title="Offline", triggered_at=recent_timestamp,
            ),
        ])
        await session.commit()

    # Roda a limpeza com batch pequeno para exercitar o loop de lotes
    summary = await run_retention_cleanup(batch_size=1)

    assert summary["positions"] >= 1
    assert summary["events"] >= 1
    assert summary["alerts"] >= 1

    async with AsyncSessionLocal() as session:
        remaining_position = await session.get(Position, recent_position_id)
        remaining_event = await session.get(Event, recent_event_id)
        remaining_alert = await session.get(Alert, recent_alert_id)

        deleted_position = await session.get(Position, old_position_id)
        deleted_event = await session.get(Event, old_event_id)
        deleted_alert = await session.get(Alert, old_alert_id)

    # Registros recentes devem permanecer
    assert remaining_position is not None
    assert remaining_event is not None
    assert remaining_alert is not None

    # Registros expirados devem ter sido removidos
    assert deleted_position is None
    assert deleted_event is None
    assert deleted_alert is None
