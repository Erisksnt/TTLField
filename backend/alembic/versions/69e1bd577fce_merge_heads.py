"""merge_heads

Revision ID: 69e1bd577fce
Revises: 055c2776d2fa, manual_add_soft_delete
Create Date: 2026-05-21 22:07:26.519921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69e1bd577fce'
down_revision: Union[str, Sequence[str], None] = ('055c2776d2fa', 'manual_add_soft_delete')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
