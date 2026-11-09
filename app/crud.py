"""
Модуль CRUD-операций (Create, Read, Update, Delete).
Содержит функции для работы с базой данных: выборка, создание, обновление
и удаление записей. Вынесение этих операций в отдельный модуль позволяет
избежать дублирования кода в роутерах и облегчает тестирование.
"""
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app import models, schemas
from app.auth import get_password_hash


# Операции с пользователями
async def get_user_by_login(db: AsyncSession, login: str):
    """Возвращает пользователя по логину или None, если пользователь не найден."""
    r = await db.execute(select(models.User).where(models.User.user_login == login))
    return r.scalar_one_or_none()


async def create_user(db: AsyncSession, user: schemas.UserCreate, role_id: int = 4):
    """Создаёт нового пользователя в базе данных."""
    db_user = models.User(
        user_login=user.user_login,
        user_password=get_password_hash(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        patronym=user.patronym,
        email=user.email,
        phone=user.phone,
        birth_date=user.birth_date,
        role_id=role_id,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# Операции с товарами
async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Возвращает список товаров с поддержкой пагинации."""
    r = await db.execute(select(models.Product).offset(skip).limit(limit))
    return r.scalars().all()


async def get_product(db: AsyncSession, product_id: int):
    """Возвращает товар по идентификатору или None."""
    r = await db.execute(
        select(models.Product).where(models.Product.product_id == product_id)
    )
    return r.scalar_one_or_none()


async def create_product(db: AsyncSession, product: schemas.ProductCreate):
    """Создаёт новую запись о товаре."""
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


async def update_product(db: AsyncSession, product_id: int, data: dict):
    """Обновляет поля товара переданными значениями."""
    product = await get_product(db, product_id)
    if not product:
        return None
    for k, v in data.items():
        setattr(product, k, v)
    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: int) -> bool:
    """Удаляет товар по идентификатору. Возвращает True при успехе."""
    product = await get_product(db, product_id)
    if not product:
        return False
    await db.delete(product)
    await db.commit()
    return True


# Операции с заказами
async def create_order(db: AsyncSession, order: schemas.OrderCreate, customer_id: int):
    """Создаёт заказ и связанные с ним позиции."""
    db_order = models.Order(
        manager_id=None,
        customer_id=customer_id,
        order_date=date.today(),
        delivery_address=order.delivery_address,
        order_status="Новый",
        payment_method=order.payment_method,
    )
    db.add(db_order)
    await db.flush()  # Получение order_id до завершения транзакции

    for item in order.items:
        product = await get_product(db, item.product_id)
        if not product or product.stock_quantity < item.quantity:
            await db.rollback()
            return None
        product.stock_quantity -= item.quantity
        db_item = models.OrderProduct(
            order_id=db_order.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            discount=item.discount,
        )
        db.add(db_item)

    await db.commit()
    return await get_order(db, db_order.order_id)


async def get_order(db: AsyncSession, order_id: int):
    """Возвращает заказ с загруженными позициями (selectinload)."""
    r = await db.execute(
        select(models.Order)
        .options(selectinload(models.Order.items))
        .where(models.Order.order_id == order_id)
    )
    return r.scalar_one_or_none()


async def get_user_orders(db: AsyncSession, user_id: int):
    """Возвращает все заказы конкретного клиента, упорядоченные по дате."""
    r = await db.execute(
        select(models.Order)
        .options(selectinload(models.Order.items))
        .where(models.Order.customer_id == user_id)
        .order_by(models.Order.order_date.desc())
    )
    return r.scalars().all()


# Операции с отзывами
async def create_review(db: AsyncSession, review: schemas.ReviewCreate, customer_id: int):
    """Создаёт отзыв клиента о товаре."""
    db_review = models.Review(
        customer_id=customer_id,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment,
        review_date=date.today(),
    )
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review


async def get_product_reviews(db: AsyncSession, product_id: int):
    """Возвращает все отзывы о конкретном товаре."""
    r = await db.execute(
        select(models.Review).where(models.Review.product_id == product_id)
    )
    return r.scalars().all()


# Инициализация справочных данных
async def init_roles(db: AsyncSession):
    """Заполняет таблицу Roles базовыми записями при первом запуске."""
    r = await db.execute(select(models.Role))
    if r.scalars().first():
        return
    roles = [
        models.Role(role_name="Менеджер по закупкам"),
        models.Role(role_name="Менеджер по продажам"),
        models.Role(role_name="Сотрудник склада"),
        models.Role(role_name="Клиент"),
    ]
    db.add_all(roles)
    await db.commit()


# Обновление профиля
async def update_user(db: AsyncSession, user_id: int, user_data: schemas.UserUpdate):
    """Обновление профиля пользователем."""
    user = await db.get(models.User, user_id)
    if not user:
        return None
        
    update_data = user_data.model_dump(exclude_unset=True, exclude_none=True)
    
    for key, value in update_data.items():
        setattr(user, key, value)
        
    await db.commit()
    await db.refresh(user)
    return user


# Управление поставщиками
async def get_all_suppliers(db: AsyncSession):
    """Получение списка всех поставщиков."""
    r = await db.execute(select(models.Supplier))
    return r.scalars().all()


async def create_supplier(db: AsyncSession, supplier: schemas.SupplierCreate):
    """Добавление нового поставщика."""
    db_supplier = models.Supplier(**supplier.model_dump())
    db.add(db_supplier)
    await db.commit()
    await db.refresh(db_supplier)
    return db_supplier


# Управление заказами
async def get_all_orders(db: AsyncSession):
    """Получение списка всех заказов."""
    r = await db.execute(
        select(models.Order)
        .options(selectinload(models.Order.items))
        .order_by(models.Order.order_date.desc())
    )
    return r.scalars().all()


async def assign_order_manager(db: AsyncSession, order_id: int, manager_id: int):
    """Назначение заказу менеджера по продажам."""
    order = await get_order(db, order_id)
    if order:
        order.manager_id = manager_id
        await db.commit()
        await db.refresh(order)
    return order


async def update_order_status(db: AsyncSession, order_id: int, status: str):
    """Обновление статуса заказа."""
    order = await get_order(db, order_id)
    if order:
        order.order_status = status
        await db.commit()
        await db.refresh(order)
    return order