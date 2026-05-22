"""merge_heads

Revision ID: bf4a16baa0b0
Revises: 69e1bd577fce
Create Date: 2026-05-21 22:08:30.517716

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf4a16baa0b0'
down_revision: Union[str, Sequence[str], None] = '69e1bd577fce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
