"""
Модуль зависимостей FastAPI.
Содержит функции, автоматически вызываемые фреймворком перед обработкой запроса. 
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app import models
from app.auth import decode_token


# Определяет эндпоинт аутентификации для отображения в Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> models.User:
    """Возвращает текущего аутентифицированного пользователя."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    login = decode_token(token)
    if not login:
        raise exc
    result = await db.execute(
        select(models.User).where(models.User.user_login == login)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise exc
    return user


async def get_current_manager(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Проверяет наличие у пользователя прав менеджера."""
    if current_user.role_id not in (1, 2):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return current_user