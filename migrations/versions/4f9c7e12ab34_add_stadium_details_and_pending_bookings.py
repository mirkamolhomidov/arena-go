"""add stadium details and pending bookings

Revision ID: 4f9c7e12ab34
Revises: 8d9e4b6c1a2f
Create Date: 2026-03-31 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4f9c7e12ab34'
down_revision: Union[str, Sequence[str], None] = '8d9e4b6c1a2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_BOOKING_STATUS = postgresql.ENUM(
    'PENDING',
    'CONFIRMED',
    'CANCELLED',
    name='bookingstatus_new',
)
OLD_BOOKING_STATUS = postgresql.ENUM(
    'CONFIRMED',
    'CANCELLED',
    name='bookingstatus_old',
)


FIELD_SIZE_CHECK = "field_size IS NULL OR field_size IN ('5x5', '6x6', '7x7')"
CONDITION_SCORE_CHECK = (
    "condition_score IS NULL OR (condition_score >= 0 AND condition_score <= 10)"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('stadiums', sa.Column('field_size', sa.String(length=10), nullable=True))
    op.add_column('stadiums', sa.Column('condition_score', sa.Integer(), nullable=True))
    op.add_column('stadiums', sa.Column('amenities', sa.Text(), nullable=True))
    op.create_check_constraint(
        'ck_stadiums_field_size_valid',
        'stadiums',
        FIELD_SIZE_CHECK,
    )
    op.create_check_constraint(
        'ck_stadiums_condition_score_valid',
        'stadiums',
        CONDITION_SCORE_CHECK,
    )
    op.drop_column('stadiums', 'end_time')
    op.drop_column('stadiums', 'start_time')

    NEW_BOOKING_STATUS.create(op.get_bind(), checkfirst=False)
    op.alter_column('bookings', 'status', server_default=None)
    op.execute(
        "ALTER TABLE bookings "
        "ALTER COLUMN status TYPE bookingstatus_new "
        "USING status::text::bookingstatus_new"
    )
    op.execute('DROP TYPE bookingstatus')
    op.execute('ALTER TYPE bookingstatus_new RENAME TO bookingstatus')
    op.alter_column(
        'bookings',
        'status',
        existing_type=postgresql.ENUM(
            'PENDING',
            'CONFIRMED',
            'CANCELLED',
            name='bookingstatus',
        ),
        server_default='PENDING',
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'stadiums',
        sa.Column('start_time', sa.Time(), nullable=False, server_default='00:00:00'),
    )
    op.add_column(
        'stadiums',
        sa.Column('end_time', sa.Time(), nullable=False, server_default='23:59:00'),
    )
    op.alter_column('stadiums', 'start_time', server_default=None)
    op.alter_column('stadiums', 'end_time', server_default=None)
    op.drop_constraint('ck_stadiums_condition_score_valid', 'stadiums', type_='check')
    op.drop_constraint('ck_stadiums_field_size_valid', 'stadiums', type_='check')
    op.drop_column('stadiums', 'amenities')
    op.drop_column('stadiums', 'condition_score')
    op.drop_column('stadiums', 'field_size')

    OLD_BOOKING_STATUS.create(op.get_bind(), checkfirst=False)
    op.execute("UPDATE bookings SET status = 'CANCELLED' WHERE status = 'PENDING'")
    op.alter_column('bookings', 'status', server_default=None)
    op.execute(
        "ALTER TABLE bookings "
        "ALTER COLUMN status TYPE bookingstatus_old "
        "USING status::text::bookingstatus_old"
    )
    op.execute('DROP TYPE bookingstatus')
    op.execute('ALTER TYPE bookingstatus_old RENAME TO bookingstatus')
