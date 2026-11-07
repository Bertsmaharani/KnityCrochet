"""
Модуль подключения к базе данных.

Реализует асинхронное взаимодействие с СУБД PostgreSQL посредством SQLAlchemy 2.0.
Асинхронный подход выбран в связи с тем, что фреймворк FastAPI функционирует
в асинхронном режиме, и синхронные запросы к базе данных снижали бы общую
производительность системы.
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


# Асинхронный движок — основной объект для выполнения запросов к базе данных
engine = create_async_engine(settings.database_url, echo=False)

# Фабрика сессий. Каждый HTTP-запрос получает собственную сессию,
# что обеспечивает изоляцию транзакций между пользователями
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Базовый класс для всех ORM-моделей.

    Наследование от данного класса позволяет SQLAlchemy автоматически
    регистрировать модели в метаданных и сопоставлять их с таблицами БД.
    """
    pass


async def get_db():
    """
    Зависимость FastAPI для предоставления сессии базы данных.

    Открывает сессию на время обработки запроса и гарантированно закрывает её
    после формирования ответа, что предотвращает утечку соединений.
    """
    async with async_session_maker() as session:
        yield session