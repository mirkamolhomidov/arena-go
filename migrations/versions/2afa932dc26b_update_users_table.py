"""update users table

Revision ID: 2afa932dc26b
Revises: 1e5b557a2f3b
Create Date: 2026-01-14 15:51:28.621111

"""
from typing import Sequence, Union

from alembic import op
import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '2afa932dc26b'
down_revision: Union[str, Sequence[str], None] = '1e5b557a2f3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role_enum = postgresql.ENUM(
    'user',
    'admin',
    'superadmin',
    name='user_role_enum'
)

def upgrade() -> None:
    # ENUM type create
    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'users',
        sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(
            length=50), nullable=False)
    )
    op.add_column(
        'users',
        sa.Column('telegram_id', sa.Integer(), nullable=False)
    )
    op.add_column(
        'users',
        sa.Column(
            'role',
            user_role_enum,
            server_default='user',
            nullable=False
        )
    )

    op.drop_index(
        op.f('idx_users_last_location'),
        table_name='users',
        postgresql_using='gist'
    )
    op.create_index(
        op.f('ix_users_telegram_id'),
        'users',
        ['telegram_id'],
        unique=True
    )
    op.drop_column('users', 'last_location')
    # ### end Alembic commands ###


def downgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'last_location',
            geoalchemy2.types.Geography(
                geometry_type='POINT',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography',
                _spatial_index_reflected=True
            ),
            autoincrement=False,
            nullable=True
        )
    )

    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.create_index(
        op.f('idx_users_last_location'),
        'users',
        ['last_location'],
        unique=False,
        postgresql_using='gist'
    )

    op.drop_column('users', 'role')
    op.drop_column('users', 'telegram_id')
    op.drop_column('users', 'phone')

    # ENUM type drop
    user_role_enum.drop(op.get_bind(), checkfirst=True)
    # ### end Alembic commands ###
