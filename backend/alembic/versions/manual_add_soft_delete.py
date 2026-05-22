## backend/alembic/versions/manual_add_soft_delete.py
"""add soft delete columns

Revision ID: manual_add_soft_delete
Revises: e24f870419e2
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'manual_add_soft_delete'
down_revision: Union[str, None] = 'e24f870419e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar coluna deleted_at nas tabelas
    op.add_column('technicians', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('geofences', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('alerts', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('positions', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('devices', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    
    # Criar índices
    op.create_index('idx_technicians_deleted_at', 'technicians', ['deleted_at'])
    op.create_index('idx_geofences_deleted_at', 'geofences', ['deleted_at'])
    op.create_index('idx_alerts_deleted_at', 'alerts', ['deleted_at'])
    op.create_index('idx_positions_deleted_at', 'positions', ['deleted_at'])


def downgrade() -> None:
    # Remover índices
    op.drop_index('idx_technicians_deleted_at', table_name='technicians')
    op.drop_index('idx_geofences_deleted_at', table_name='geofences')
    op.drop_index('idx_alerts_deleted_at', table_name='alerts')
    op.drop_index('idx_positions_deleted_at', table_name='positions')
    
    # Remover colunas
    op.drop_column('technicians', 'deleted_at')
    op.drop_column('geofences', 'deleted_at')
    op.drop_column('alerts', 'deleted_at')
    op.drop_column('positions', 'deleted_at')
    op.drop_column('users', 'deleted_at')
    op.drop_column('devices', 'deleted_at')