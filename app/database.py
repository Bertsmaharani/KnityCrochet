"""
Модуль подключения к базе данных.
Реализует асинхронное взаимодействие с СУБД PostgreSQL посредством SQLAlchemy 2.0.
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


# Асинхронный движок — основной объект для выполнения запросов к базе данных
engine = create_async_engine(settings.database_url, echo=False)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


async def get_db():
    """Зависимость FastAPI для предоставления сессии базы данных."""
    async with async_session_maker() as session:
        yield session

        