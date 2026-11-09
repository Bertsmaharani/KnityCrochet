"""
Модуль маршрутов для работы с пользователями.
Реализует регистрацию, аутентификацию (вход) и управление
профилем текущего пользователя. Пароли хранятся в зашифрованном виде.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import schemas, crud, auth, models
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["Пользователи"])


@router.post("/register", response_model=schemas.UserOut, status_code=201)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация нового клиента."""
    # Проверка, не занят ли логин
    existing = await crud.get_user_by_login(db, user.user_login)
    if existing:
        raise HTTPException(status_code=400, detail="Логин уже занят")
    
    try:
        # роль_id=4 — «Клиент»
        return await crud.create_user(db, user, role_id=4)
    except ValueError as e:
        # Перехватываем ошибку слишком длинного пароля
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # Общая обработка ошибок 
        raise HTTPException(status_code=400, detail="Ошибка регистрации. Проверьте введенные данные.")


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Аутентификация пользователя и выдача JWT-токена."""
    # Ищем пользователя по логину
    user = await crud.get_user_by_login(db, form_data.username)
    
    # Проверяем существование пользователя и корректность пароля
    if not user or not auth.verify_password(form_data.password, user.user_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Генерируем токен, сохраняя в него логин (sub)
    token = auth.create_access_token({"sub": user.user_login})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
async def read_me(current_user: models.User = Depends(get_current_user)):
    """Получение данных текущего авторизованного пользователя."""
    return current_user


@router.put("/me", response_model=schemas.UserOut)
async def update_profile(
    user_data: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Обновление личных данных текущего пользователя."""
    return await crud.update_user(db, current_user.user_id, user_data)