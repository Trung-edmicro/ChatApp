"""create_prompt_table

Revision ID: 718123c63d32
Revises: 20507ea70508
Create Date: 2025-02-28 16:25:30.282564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '718123c63d32'
down_revision: Union[str, None] = '20507ea70508'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('prompts',
        sa.Column('prompt_id', sa.String(), primary_key=True, index=True), # Bỏ length=255, index=True
        sa.Column('name', sa.String()), # Bỏ length=255
        sa.Column('content', sa.String()), # Bỏ length=255
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')) # DateTime không timezone
    )


def downgrade() -> None:
    op.drop_table('prompts')
