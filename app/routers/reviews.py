"""
Модуль маршрутов для работы с отзывами.
Позволяет клиентам оставлять отзывы о товарах и получать список существующих отзывов по конкретному товару.
"""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import schemas, crud
from app.dependencies import get_current_user
from app import models


router = APIRouter(prefix="/api/reviews", tags=["Отзывы"])


@router.post("/", response_model=schemas.ReviewOut, status_code=201)
async def create(
    review: schemas.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Создание отзыва."""
    product = await crud.get_product(db, review.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return await crud.create_review(db, review, customer_id=current_user.user_id)


@router.get("/product/{product_id}", response_model=list[schemas.ReviewOut])
async def product_reviews(
    product_id: int = Path(..., ge=1, le=2147483647),
    db: AsyncSession = Depends(get_db)):
    """Получение всех отзывов по указанному товару. Доступно без аутентификации."""
    return await crud.get_product_reviews(db, product_id)

