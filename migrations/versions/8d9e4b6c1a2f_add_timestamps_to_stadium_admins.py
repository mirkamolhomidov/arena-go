"""add timestamps to stadium_admins

Revision ID: 8d9e4b6c1a2f
Revises: 1f51c7642d08
Create Date: 2026-03-29 15:58:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8d9e4b6c1a2f"
down_revision: Union[str, Sequence[str], None] = "1f51c7642d08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timestamp columns to the stadium_admins table."""
    op.add_column(
        "stadium_admins",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "stadium_admins",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove timestamp columns from the stadium_admins table."""
    op.drop_column("stadium_admins", "updated_at")
    op.drop_column("stadium_admins", "created_at")
