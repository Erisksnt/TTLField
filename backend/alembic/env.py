## backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

# Adicionar o diretório backend ao path para importar os modelos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importar seus modelos e configurações
from app.database import Base
from app.config import get_settings
from app.models.user import User
from app.models.technician import Technician
from app.models.position import Position
from app.models.geofence import Geofence
from app.models.alert import Alert

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# IMPORTANTE: Usar os metadados dos seus modelos
target_metadata = Base.metadata

# Obter URL do banco das configurações
settings = get_settings()
database_url = settings.database_url.replace("postgresql://", "postgresql+psycopg2://")

# Configurar a URL do banco
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import create_engine
    from app.config import get_settings

    settings = get_settings()
    # Converte a URL assíncrona para síncrona (remove +asyncpg)
    sync_url = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://')
    connectable = create_engine(sync_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
