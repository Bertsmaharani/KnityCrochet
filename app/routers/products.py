"""
Модуль маршрутов для работы с товарами.

Реализует полный набор CRUD-операций. Операции создания, изменения
и удаления защищены проверкой прав (доступны только менеджерам).
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app import models, schemas, crud
from app.dependencies import get_current_manager, get_current_user


router = APIRouter(prefix="/api/products", tags=["Товары"])

# Константа для максимального значения типа INTEGER в PostgreSQL
MAX_INT = 2147483647
# Константа для максимального значения типа BIGINT в PostgreSQL (защита от переполнения)
MAX_BIGINT = 9223372036854775807


# Маршруты поставщиков должны идти СТРОГО ВЫШЕ, чем /{product_id}
@router.get("/suppliers/all", response_model=list[schemas.SupplierOut])
async def get_suppliers(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Получение списка поставщиков менеджером по закупкам."""
    if current_user.role_id != 1: 
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return await crud.get_all_suppliers(db)


@router.post("/suppliers/create", response_model=schemas.SupplierOut)
async def create_supplier_endpoint(
    supplier: schemas.SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Добавление нового поставщика менеджером по закупкам."""
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return await crud.create_supplier(db, supplier)


# Маршруты для работы с товарами
@router.get("/", response_model=list[schemas.ProductOut])
async def list_products(
    # Добавлено ограничение le=MAX_BIGINT для защиты базы данных от переполнения
    skip: int = Query(0, ge=0, le=MAX_BIGINT), 
    limit: int = Query(100, ge=1, le=MAX_BIGINT), 
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка товаров.

    Поддерживает пагинацию через параметры skip (пропуск) и limit (ограничение).
    Доступно всем пользователям без аутентификации.
    """
    return await crud.get_products(db, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=schemas.ProductOut)
async def get_one(
    product_id: int = Path(..., ge=1, le=MAX_INT), 
    db: AsyncSession = Depends(get_db)
):
    """Получение товара по идентификатору. При отсутствии — ошибка 404."""
    product = await crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product


@router.post("/", response_model=schemas.ProductOut, status_code=201)
async def create(
    product: schemas.ProductCreate,
    db: AsyncSession = Depends(get_db),
    _manager=Depends(get_current_manager),
):
    """Создание нового товара. Доступно только менеджерам."""
    return await crud.create_product(db, product)


@router.patch("/{product_id}", response_model=schemas.ProductOut)
async def update(
    product_id: int = Path(..., ge=1, le=MAX_INT),
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    _manager=Depends(get_current_manager),
):
    """
    Частичное обновление информации о товаре.
    """
    if not data:
        raise HTTPException(status_code=400, detail="Данные для обновления не переданы")
        
    product = await crud.update_product(db, product_id, data)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product


@router.delete("/{product_id}", status_code=204)
async def remove(
    product_id: int = Path(..., ge=1, le=MAX_INT),
    db: AsyncSession = Depends(get_db),
    _manager=Depends(get_current_manager),
):
    """Удаление товара. Возвращает код 204 (No Content) при успехе."""
    try:
        if not await crud.delete_product(db, product_id):
            raise HTTPException(status_code=404, detail="Товар не найден")
    except IntegrityError:
        # Если товар уже используется в заказах (Foreign Key), откатываем транзакцию
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Невозможно удалить товар, так как он присутствует в заказах."
        )