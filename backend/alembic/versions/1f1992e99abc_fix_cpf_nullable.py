"""fix_cpf_nullable

Revision ID: 1f1992e99abc
Revises: e244ded9c0d5
Create Date: 2026-05-25 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1f1992e99abc'
down_revision = 'e244ded9c0d5'
branch_labels = None
depends_on = None


def upgrade():
    # Apenas tornar a coluna nullable (sem dropar constraint que não existe)
    op.alter_column('technicians', 'cpf', nullable=True)
    # Remover dados vazios antes de alterar
    op.execute("UPDATE technicians SET cpf = NULL WHERE cpf = ''")
    # Alterar coluna para nullable
    op.alter_column('technicians', 'cpf', existing_type=sa.String(), nullable=True)


def downgrade():
    op.alter_column('technicians', 'cpf', nullable=False)