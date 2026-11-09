"""
Модуль Pydantic-схем для валидации данных.
Схемы описывают структуру данных, принимаемых от клиента и возвращаемых
в ответе.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from decimal import Decimal

# Максимальное значение для типа INTEGER в PostgreSQL
MAX_ID = 2147483647


class RoleOut(BaseModel):
    """Схема для вывода информации о роли."""
    role_id: int
    role_name: str
    class Config:
        from_attributes = True  # Позволяет создавать схему из ORM-объекта


class UserCreate(BaseModel):
    """Схема регистрации нового пользователя."""
    user_login: str = Field(..., min_length=3, max_length=50)
    # Запрещаем нулевые байты и ограничиваем длину пароля для bcrypt
    password: str = Field(..., min_length=6, max_length=72, pattern=r"^[^\x00]*$")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    patronym: str | None = Field(None, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=20)
    birth_date: date


class UserOut(BaseModel):
    """Схема вывода данных пользователя."""
    user_id: int
    user_login: str
    first_name: str
    last_name: str
    patronym: str | None = None
    email: EmailStr
    phone: str
    role_id: int | None = None
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Схема ответа при успешной аутентификации."""
    access_token: str
    token_type: str


class SupplierCreate(BaseModel):
    """Схема создания нового поставщика."""
    supplier_name: str = Field(..., min_length=1, max_length=255)
    contact_info: str = Field(..., min_length=1, max_length=255)
    manager_id: int = Field(..., ge=1, le=MAX_ID)


class SupplierOut(SupplierCreate):
    """Схема вывода информации о поставщике."""
    supplier_id: int
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Базовая схема товара."""
    product_name: str = Field(..., min_length=2, max_length=255)
    category_name: str = Field(..., min_length=1, max_length=255)
    # max_digits и decimal_places защищают от переполнения NUMERIC(10, 2) в БД
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    stock_quantity: int = Field(..., ge=0, le=MAX_ID)
    supplier_id: int = Field(..., ge=1, le=MAX_ID)


class ProductCreate(ProductBase):
    """Схема создания товара (совпадает с базовой)."""
    pass


class ProductOut(ProductBase):
    """Схема вывода товара (добавляет идентификатор)."""
    product_id: int
    class Config:
        from_attributes = True


class OrderProductCreate(BaseModel):
    """Схема позиции в заказе: товар, количество, скидка."""
    product_id: int = Field(..., ge=1, le=MAX_ID)
    quantity: int = Field(..., ge=1, le=MAX_ID)
    discount: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, max_digits=5, decimal_places=2)


class OrderProductOut(OrderProductCreate):
    """Схема вывода позиции заказа."""
    order_product_id: int
    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """Схема оформления заказа: адрес, способ оплаты и перечень позиций."""
    delivery_address: str = Field(..., min_length=5, max_length=500)
    payment_method: str = Field(..., min_length=1, max_length=100)
    # min_length=1 требует, чтобы в заказе был хотя бы один товар
    items: list[OrderProductCreate] = Field(..., min_length=1)


class OrderOut(BaseModel):
    """Схема вывода информации о заказе."""
    order_id: int
    customer_id: int
    manager_id: int | None = None
    order_date: date
    delivery_address: str
    order_status: str
    payment_method: str
    items: list[OrderProductOut] = []
    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    """Схема создания отзыва."""
    product_id: int = Field(..., ge=1, le=MAX_ID)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=3, max_length=1000, pattern=r"^[^\x00]*$")


class ReviewOut(ReviewCreate):
    """Схема вывода отзыва."""
    review_id: int
    customer_id: int
    review_date: date
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Обновление профиля"""
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    patronym: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, min_length=1, max_length=20)


class OrderUpdateManager(BaseModel):
    """Управление заказами"""
    manager_id: int = Field(..., ge=1, le=MAX_ID)


class OrderUpdateStatus(BaseModel):
    """Управление статусами заказов"""
    order_status: str = Field(..., min_length=1, max_length=100)