"""
Конфигурация Alembic для асинхронного SQLAlchemy.

Скрипт выполняется Alembic при каждой миграции. Обеспечивает:
- подключение к базе данных через строку из .env;
- автоматическое обнаружение ORM-моделей из app/models.py;
- сравнение текущей схемы БД с моделями и генерацию миграций.
"""
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Добавляем корневую директорию в sys.path,
# чтобы импортировать модули приложения (app.models, app.config)
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import *  # noqa — важно для регистрации всех моделей
from app.config import settings


# Объект конфигурации Alembic (читает alembic.ini)
config = context.config

# Переопределяем URL БД значением из .env
config.set_main_option("sqlalchemy.url", settings.database_url)

# Настройка логирования из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные, по которым Alembic определяет изменения
target_metadata = Base.metadata


def run_migrations_offline():
    """Режим генерации SQL без подключения к БД (используется редко)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection):
    """Применяет миграции через переданное соединение."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """
    Асинхронный режим применения миграций.
    Необходим, так как проект использует asyncpg.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    """Точка входа для online-режима."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()