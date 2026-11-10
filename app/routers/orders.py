"""
Модуль маршрутов для работы с заказами.
Реализует оформление заказов и просмотр истории заказов.
Все операции требуют аутентификации.
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import schemas, crud
from app.dependencies import get_current_user
from app import models

# Константа для максимального значения типа INTEGER в PostgreSQL
MAX_ID = 2147483647

router = APIRouter(prefix="/api/orders", tags=["Заказы"])


@router.post("/", response_model=schemas.OrderOut, status_code=201)
async def create(
    order: schemas.OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Оформление нового заказа."""
    db_order = await crud.create_order(db, order, customer_id=current_user.user_id)
    if not db_order:
        raise HTTPException(
            status_code=400,
            detail="Не удалось создать заказ: проверьте наличие товаров на складе",
        )
    return db_order


@router.get("/my", response_model=list[schemas.OrderOut])
async def my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Возвращает историю заказов текущего пользователя."""
    return await crud.get_user_orders(db, current_user.user_id)


@router.get("/all", response_model=list[schemas.OrderOut])
async def get_all_orders(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Получение списка всех заказов для менеджера по продажам."""
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return await crud.get_all_orders(db)


@router.get("/{order_id}", response_model=schemas.OrderOut)
async def get_one(
    order_id: int = Path(..., ge=1, le=MAX_ID),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Получение заказа по идентификатору."""
    order = await crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    if order.customer_id != current_user.user_id and current_user.role_id not in (1, 2):
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return order


@router.patch("/{order_id}/manager", response_model=schemas.OrderOut)
async def assign_manager(
    order_id: int = Path(..., ge=1, le=MAX_ID),
    data: schemas.OrderUpdateManager = Body(...), 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Изменение менеджера по продажам у заказа по его идентификатору."""
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
        
    try:
        order = await crud.assign_order_manager(db, order_id, data.manager_id)
        if not order: 
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return order
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Указанный менеджер не существует.")

@router.patch("/{order_id}/status", response_model=schemas.OrderOut)
async def change_status(
    order_id: int = Path(..., ge=1, le=MAX_ID),
    data: schemas.OrderUpdateStatus = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Изменение статуса заказа по его идентификатору."""
    if current_user.role_id != 2:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    order = await crud.update_order_status(db, order_id, data.order_status)
    if not order: 
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order