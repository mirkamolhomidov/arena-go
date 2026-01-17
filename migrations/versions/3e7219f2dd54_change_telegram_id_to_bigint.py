"""change telegram_id to bigint

Revision ID: 3e7219f2dd54
Revises: c2fc28a673a7
Create Date: 2026-01-14 17:15:05.150332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e7219f2dd54'
down_revision: Union[str, Sequence[str], None] = 'c2fc28a673a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'users',
        'telegram_id',
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        'users',
        'telegram_id',
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False
    )
