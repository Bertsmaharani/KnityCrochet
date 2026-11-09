"""
Модуль тестирования API на основе свойств (property-based testing).
Цель — выявить ситуации, при которых сервер возвращает ошибку 500
(внутренняя ошибка), что свидетельствует о непредвиденном поведении
и необходимости доработки обработки ошибок.
"""
import schemathesis

# Загрузка OpenAPI-схемы из работающего экземпляра приложения.
schema = schemathesis.from_uri("http://127.0.0.1:8000/openapi.json")


@schema.parametrize()
def test_api(case):
    """Универсальный тест для всех эндпоинтов API."""
    response = case.call()
    # Проверка соответствия ответа заявленной в схеме спецификации
    case.validate_response(response)