"""merge_heads

Revision ID: abb8cc2152ea
Revises: bf4a16baa0b0
Create Date: 2026-05-21 22:08:47.040338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abb8cc2152ea'
down_revision: Union[str, Sequence[str], None] = 'bf4a16baa0b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
