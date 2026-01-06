import os
import sys
from dotenv import load_dotenv
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel
from app.core.config import settings

# MUHIM: Avval load_dotenv
load_dotenv()

# MUHIM: Python path ga loyiha papkasini qo'shamiz
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MUHIM: Import LOAD_DOTENV dan keyin va to'g'ri tartibda
from app.models.regions import Regions
from app.models.districts import Districts
from app.models.local_areas import LocalAreas
from app.models.stadiums import Stadiums
from app.models.users import Users
from app.models.stadium_images import StadiumImages
from app.models.admins import Admins
from app.models.bookings import Bookings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

DATABASE_URL = settings.DATABASE_URL_SYNC

def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()