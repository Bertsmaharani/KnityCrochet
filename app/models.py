"""
Модуль ORM-моделей базы данных.

Содержит описание семи таблиц в соответствии с ER-диаграммой,
разработанной в курсовой работе: Roles, Users, Suppliers, Products,
Orders, OrderProducts, Reviews.

Каждый класс представляет отдельную таблицу, атрибуты класса — её столбцы.
Отношения (relationship) реализуют связи между таблицами, определённые
при проектировании базы данных.
"""
from sqlalchemy import (
    Column, Integer, Text, Numeric, Date, ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Role(Base):
    """
    Таблица ролей пользователей.

    Содержит четыре роли в соответствии с предметной областью:
    менеджер по закупкам, менеджер по продажам, сотрудник склада, клиент.
    """
    __tablename__ = "Roles"

    role_id = Column(Integer, primary_key=True, index=True)  # Первичный ключ
    role_name = Column(Text, nullable=False)                 # Наименование роли

    # Связь "один ко многим": одна роль — множество пользователей
    users = relationship("User", back_populates="role")


class User(Base):
    """
    Таблица пользователей системы.

    Объединяет сотрудников организации и клиентов.
    Пароли хранятся в виде хеша (алгоритм bcrypt), что исключает
    возможность их восстановления в открытом виде.
    """
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("Roles.role_id"))   # Внешний ключ на таблицу Roles
    user_login = Column(Text, unique=True, nullable=False)   # Уникальный логин
    user_password = Column(Text, nullable=False)             # Хеш пароля
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    patronym = Column(Text, nullable=True)                   # Отчество (необязательное поле)
    email = Column(Text, nullable=False)
    phone = Column(Text, nullable=False)
    birth_date = Column(Date, nullable=False)

    # Связи с другими таблицами
    role = relationship("Role", back_populates="users")
    managed_suppliers = relationship("Supplier", back_populates="manager")
    managed_orders = relationship(
        "Order", foreign_keys="Order.manager_id", back_populates="manager"
    )
    customer_orders = relationship(
        "Order", foreign_keys="Order.customer_id", back_populates="customer"
    )
    reviews = relationship("Review", back_populates="customer")


class Supplier(Base):
    """
    Таблица поставщиков товаров.

    Содержит информацию о контрагентах, поставляющих продукцию в магазин.
    Каждый поставщик закреплён за конкретным менеджером по закупкам.
    """
    __tablename__ = "Suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("Users.user_id"))
    supplier_name = Column(Text, nullable=False)
    contact_info = Column(Text, nullable=False)

    manager = relationship("User", back_populates="managed_suppliers")
    products = relationship("Product", back_populates="supplier")


class Product(Base):
    """
    Таблица товаров.

    Содержит ассортимент магазина: пряжу, инструменты, книги, фурнитуру и т. д.
    Учитывает остатки на складе и стоимость единицы товара.
    """
    __tablename__ = "Products"

    product_id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("Suppliers.supplier_id"))
    product_name = Column(Text, nullable=False)
    category_name = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)           # Цена с точностью до копеек
    stock_quantity = Column(Integer, nullable=False)         # Остаток на складе

    supplier = relationship("Supplier", back_populates="products")
    order_items = relationship("OrderProduct", back_populates="product")
    reviews = relationship("Review", back_populates="product")


class Order(Base):
    """
    Таблица заказов.

    Фиксирует факт оформления заказа клиентом и содержит сведения
    о доставке, способе оплаты и текущем статусе обработки.
    """
    __tablename__ = "Orders"

    order_id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("Users.user_id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("Users.user_id"))
    order_date = Column(Date, nullable=False)
    delivery_address = Column(Text, nullable=False)
    order_status = Column(Text, nullable=False)
    payment_method = Column(Text, nullable=False)

    manager = relationship(
        "User", foreign_keys=[manager_id], back_populates="managed_orders"
    )
    customer = relationship(
        "User", foreign_keys=[customer_id], back_populates="customer_orders"
    )
    # Каскадное удаление позиций при удалении заказа
    items = relationship(
        "OrderProduct", back_populates="order", cascade="all, delete-orphan"
    )


class OrderProduct(Base):
    """
    Таблица состава заказа.

    Реализует связь "многие ко многим" между заказами и товарами
    с дополнительными атрибутами: количеством и величиной скидки.
    """
    __tablename__ = "OrderProducts"

    order_product_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("Orders.order_id"))
    product_id = Column(Integer, ForeignKey("Products.product_id"))
    quantity = Column(Integer, nullable=False)
    discount = Column(Numeric(5, 2), nullable=False, default=0)  # Скидка в процентах

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Review(Base):
    """
    Таблица отзывов клиентов.

    Обеспечивает обратную связь: клиент может оставить оценку
    и текстовый комментарий к приобретённому товару.
    """
    __tablename__ = "Reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("Users.user_id"))
    product_id = Column(Integer, ForeignKey("Products.product_id"))
    rating = Column(Integer, nullable=False)                 # Оценка от 1 до 5
    comment = Column(Text, nullable=False)
    review_date = Column(Date, nullable=False)

    customer = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")