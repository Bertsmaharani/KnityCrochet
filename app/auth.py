"""
Модуль аутентификации и работы с паролями.

Содержит функции для хеширования и проверки паролей (совместимые с Django),
а также для создания и декодирования JWT-токенов.
"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Настраиваем контекст для хеширования паролей.
# Используем bcrypt_sha256 (обходит лимит в 72 байта), 
# а также поддерживаем старые хеши bcrypt и django_pbkdf2_sha256 (для совместимости).
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt", "django_pbkdf2_sha256"], 
    deprecated="auto"
)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Проверяет соответствие введенного пароля хешу из базы данных.
    
    Если хеш не распознан (например, пароль был сохранен как обычный текст),
    выполняется прямое сравнение строк (для обратной совместимости).
    """
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        # Fallback: если passlib не смог распознать формат, сравниваем напрямую
        return plain == hashed


def get_password_hash(password: str) -> str:
    """
    Создает хеш пароля для безопасного хранения в БД.
    
    Использование bcrypt_sha256 позволяет хешировать пароли любой длины
    без риска возникновения ошибки переполнения.
    """
    try:
        return pwd_context.hash(password)
    except ValueError:
        # Оставляем защиту на случай непредвиденных ошибок
        raise ValueError("Недопустимый пароль. Проверьте введенные данные.")


def create_access_token(data: dict) -> str:
    """
    Создает JWT-токен с указанными данными (обычно {'sub': login}).
    
    Токен автоматически получает срок жизни (exp), равный значению
    ACCESS_TOKEN_EXPIRE_MINUTES из настроек.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> str | None:
    """
    Декодирует JWT-токен и извлекает из него логин пользователя (поле 'sub').
    
    Возвращает None, если токен недействителен (просрочен или подделан).
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None