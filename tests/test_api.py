"""
Модуль модульных тестов API.
Проверяет корректность работы основных эндпоинтов средствами
библиотеки pytest и асинхронного клиента HTTPX.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

BASE = "http://test"


@pytest.mark.asyncio
async def test_index_works():
    """Проверка доступности главной страницы (код ответа 200)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        r = await ac.get("/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_products():
    """Проверка эндпоинта получения списка товаров."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        r = await ac.get("/api/products/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_get_product_not_found():
    """Проверка обработки ситуации, когда товар не найден (код 404)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        r = await ac.get("/api/products/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_register_short_password():
    """Проверка валидации."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        r = await ac.post("/api/users/register", json={
            "user_login": "test_user_x",
            "password": "123",
            "first_name": "Test",
            "last_name": "Test",
            "email": "t@t.ru",
            "phone": "123",
            "birth_date": "2000-01-01",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_wrong_credentials():
    """Проверка отказа в доступе при неверных учётных данных (код 401)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        r = await ac.post("/api/users/login", data={
            "username": "nonexistent",
            "password": "wrong"
        })
    assert r.status_code == 401