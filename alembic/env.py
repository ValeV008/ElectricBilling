import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool


config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models metadata
from app.db.base import Base  # noqa

import app.db.models  # noqa

target_metadata = Base.metadata

# NEW: override sqlalchemy.url from env if present
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
