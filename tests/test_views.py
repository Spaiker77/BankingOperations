import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import generate_response


# Общие моки для всех тестов
@pytest.fixture
def mock_dependencies():
    with (
        patch("src.views.load_user_settings") as mock_settings,
        patch("src.views.load_transactions") as mock_trans,
        patch("src.views.filter_transactions_by_date") as mock_filter,
        patch("src.views.calculate_card_stats") as mock_cards,
        patch("src.views.get_top_transactions") as mock_top,
        patch("src.views.fetch_currency_rates") as mock_curr,
        patch("src.views.fetch_stock_prices") as mock_stock,
    ):

        # Стандартные возвращаемые значения
        mock_settings.return_value = {
            "user_currencies": ["USD"],
            "user_stocks": ["AAPL"],
            "alpha_vantage_api_key": "test",
        }
        # Создаем DataFrame с правильными названиями колонок
        mock_trans.return_value = pd.DataFrame(
            columns=[
                "Дата операции",
                "Дата платежа",
                "Номер карты",
                "Статус",
                "Сумма операции",
                "Валюта операции",
                "Сумма платежа",
                "Валюта платежа",
                "Кэшбэк",
                "Категория",
                "MCC",
                "Описание",
                "Бонусы (включая кэшбэк)",
                "Округление на инвесткопилку",
                "Сумма операции с округлением",
            ]
        )
        mock_filter.return_value = pd.DataFrame(
            columns=[
                "Дата операции",
                "Дата платежа",
                "Номер карты",
                "Статус",
                "Сумма операции",
                "Валюта операции",
                "Сумма платежа",
                "Валюта платежа",
                "Кэшбэк",
                "Категория",
                "MCC",
                "Описание",
                "Бонусы (включая кэшбэк)",
                "Округление на инвесткопилку",
                "Сумма операции с округлением",
            ]
        )
        mock_cards.return_value = []
        mock_top.return_value = []
        mock_curr.return_value = []
        mock_stock.return_value = []

        yield {
            "settings": mock_settings,
            "trans": mock_trans,
            "filter": mock_filter,
            "cards": mock_cards,
            "top": mock_top,
            "curr": mock_curr,
            "stock": mock_stock,
        }


# Тест приветствий
@pytest.mark.parametrize(
    "time,greeting",
    [
        ("06:00:00", "Доброе утро"),
        ("13:00:00", "Добрый день"),
        ("20:00:00", "Добрый вечер"),
        ("02:00:00", "Доброй ночи"),
    ],
)
def test_greetings(mock_dependencies, time, greeting):
    response = generate_response(f"2023-01-01 {time}")
    result = json.loads(response)
    assert result["greeting"] == greeting


# Основной тест
def test_main_flow(mock_dependencies):
    # Настройка моков
    mock_dependencies["cards"].return_value = [{"card": "data"}]
    mock_dependencies["top"].return_value = [{"transaction": "data"}]
    mock_dependencies["curr"].return_value = [{"currency": "USD"}]
    mock_dependencies["stock"].return_value = [{"stock": "AAPL"}]

    # Вызов функции
    response = generate_response("2023-01-01 12:00:00")
    result = json.loads(response)

    # Проверки
    assert "greeting" in result
    assert len(result["cards"]) == 1
    assert len(result["top_transactions"]) == 1
    assert len(result["currency_rates"]) == 1
    assert len(result["stock_prices"]) == 1


# Тест обработки ошибок
def test_error_handling():
    with patch("src.views.load_user_settings") as mock_settings:
        mock_settings.side_effect = Exception("Test error")
        response = generate_response("2023-01-01 12:00:00")
        result = json.loads(response)
        assert "error" in result
