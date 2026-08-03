"""add_geofence_events_timestamp_index

Revision ID: a1b2c3d4e5f6
Revises: 66ce9ad63a5d
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '66ce9ad63a5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Índice em geofence_events.timestamp, necessário para a rotina de
    limpeza de retenção de dados (WHERE timestamp < cutoff) rodar de
    forma performática mesmo com a tabela grande.
    """
    op.create_index(
        'idx_geofence_events_timestamp',
        'geofence_events',
        ['timestamp'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('idx_geofence_events_timestamp', table_name='geofence_events')
