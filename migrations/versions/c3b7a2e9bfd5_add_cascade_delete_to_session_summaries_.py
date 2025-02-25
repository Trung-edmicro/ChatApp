"""add_cascade_delete_to_session_summaries_relationship

Revision ID: c3b7a2e9bfd5
Revises: 2f221e52c403
Create Date: 2025-02-25 10:07:33.777272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3b7a2e9bfd5'
down_revision: Union[str, None] = '2f221e52c403'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
