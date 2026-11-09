"""
Модуль аутентификации и работы с паролями.
Содержит функции для хеширования и проверки паролей, а также для создания и декодирования JWT-токенов.
"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Настраиваем контекст для хеширования паролей.
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt", "django_pbkdf2_sha256"], 
    deprecated="auto"
)


def verify_password(plain: str, hashed: str) -> bool:
    """Проверяет соответствие введенного пароля хешу из базы данных."""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return plain == hashed


def create_access_token(data: dict) -> str:
    """Создает JWT-токен с ограниченным сроком действия."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def get_password_hash(password: str) -> str:
    """Создает хеш пароля для безопасного хранения в БД."""
    try:
        return pwd_context.hash(password)
    except ValueError:
        raise ValueError("Недопустимый пароль. Проверьте введенные данные.")


def decode_token(token: str) -> str | None:
    """Декодирует JWT-токен и извлекает из него логин пользователя (поле 'sub')."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None