"""
Главный модуль приложения.

Отвечает за:
- инициализацию FastAPI-приложения и его параметров;
- подключение статических файлов и шаблонов;
- регистрацию API-маршрутов;
- определение HTML-страниц (главная, регистрация, вход, корзина, карточка товара);
- выполнение стартовых действий (создание таблиц и заполнение справочника ролей).
"""
import os
import sys
from pathlib import Path

# Добавляем папку admin_panel в пути, чтобы Python нашел настройки Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "admin_panel"))

# Инициализация Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admin_panel.settings")
import django
django.setup()

from django.core.wsgi import get_wsgi_application
from a2wsgi import WSGIMiddleware  # Используем a2wsgi вместо starlette

django_app = get_wsgi_application()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, engine, Base
from app import crud
from app.routers import products, users, orders, reviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Обработчик событий жизненного цикла приложения.

    Выполняется при запуске сервера:
    1. Создаёт все таблицы в БД, если они ещё не существуют.
    2. Заполняет таблицу Roles базовыми записями.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.database import async_session_maker
    async with async_session_maker() as db:
        await crud.init_roles(db)
    yield


# Создание экземпляра FastAPI-приложения
app = FastAPI(title="Knity Crochet", lifespan=lifespan)

# Подключение каталога статических файлов (CSS, изображения)
os.makedirs("static/css", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация механизма шаблонов Jinja2
templates = Jinja2Templates(directory="app/templates")

# Регистрация API-маршрутов
app.include_router(products.router)
app.include_router(users.router)
app.include_router(orders.router)
app.include_router(reviews.router)


# HTML-страницы
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Главная страница — каталог товаров.

    Загружает до 12 товаров из БД и передаёт их в шаблон для отображения.
    """
    products_list = await crud.get_products(db, limit=12)
    return templates.TemplateResponse(
        request, "index.html", {"products": products_list}
    )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации нового клиента."""
    return templates.TemplateResponse(request, "register.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа в систему."""
    return templates.TemplateResponse(request, "login.html")


@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request):
    """Страница корзины и оформления заказа."""
    return templates.TemplateResponse(request, "cart.html")


@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_page(
    product_id: int = Path(..., ge=1, le=2147483647), 
    request: Request = None, 
    db: AsyncSession = Depends(get_db)
):
    """
    Страница подробной информации о товаре.

    Загружает данные товара и связанные с ним отзывы.
    """
    product = await crud.get_product(db, product_id)
    reviews_list = await crud.get_product_reviews(db, product_id)
    return templates.TemplateResponse(
        request,
        "product.html",
        {"product": product, "reviews": reviews_list},
    )


@app.get("/delivery", response_class=HTMLResponse)
async def delivery_page(request: Request):
    """Страница доставки."""
    return templates.TemplateResponse(request, "delivery.html")


@app.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request):
    """Страница контактов."""
    return templates.TemplateResponse(request, "contacts.html")

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Страница личного кабинета."""
    return templates.TemplateResponse(request, "profile.html")


# Монтируем статику Django (CSS/JS для админки)
app.mount(
    "/django-static", 
    StaticFiles(directory=str(BASE_DIR / "admin_panel" / "staticfiles")), 
    name="django-static"
)

# Монтируем саму админку Django
app.mount("/admin", WSGIMiddleware(django_app))