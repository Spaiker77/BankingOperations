import json
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock
from src.utils import load_transactions, filter_transactions_by_date, fetch_currency_rates

import pandas as pd
import pytest

from src import utils


# Тесты для get_greeting
@pytest.mark.parametrize(
    "hour,expected",
    [
        (5, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (22, "Добрый вечер"),
        (23, "Доброй ночи"),
        (4, "Доброй ночи"),
    ],
)
def test_get_greeting(hour, expected):
    test_time = datetime(2023, 1, 1, hour)
    assert utils.get_greeting(test_time) == expected


# Тесты для load_user_settings
def test_load_user_settings_success():
    mock_data = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN"],
        "alpha_vantage_api_key": "test_key",
    }
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        result = utils.load_user_settings()
        assert result == mock_data


# Тесты для fetch_stock_prices
@patch("src.utils.os.getenv")
@patch("requests.get")
def test_fetch_stock_prices_with_env_key(mock_get, mock_getenv):
    """Тест с использованием ключа из .env"""
    mock_getenv.return_value = "env_api_key"
    mock_response = MagicMock()
    mock_response.json.return_value = {"Global Quote": {"05. price": "150.25"}}
    mock_get.return_value = mock_response

    result = utils.fetch_stock_prices(["AAPL"])
    assert result[0]["price"] == 150.25


@patch("src.utils.load_user_settings")
@patch("requests.get")
def test_fetch_stock_prices_with_settings_key(mock_get, mock_load_settings):
    """Тест с использованием ключа из настроек"""
    mock_settings = {"alpha_vantage_api_key": "settings_key"}
    mock_load_settings.return_value = mock_settings

    mock_response = MagicMock()
    mock_response.json.return_value = {"Global Quote": {"05. price": "200.00"}}
    mock_get.return_value = mock_response

    result = utils.fetch_stock_prices(["AMZN"])
    assert result[0]["price"] == 200.00


# Тесты для calculate_card_stats
@pytest.mark.parametrize(
    "data,expected",
    [
        (
            [["1234****5678", "-500,00"], ["1234****5678", "-300,50"]],
            [{"last_digits": "5678", "total_spent": 800.50, "cashback": 8.01}],
        ),
        (
            [["1234****5678", "-200,00"], ["9876****5432", "-100,00"]],
            [
                {"last_digits": "5678", "total_spent": 200.00, "cashback": 2.00},
                {"last_digits": "5432", "total_spent": 100.00, "cashback": 1.00},
            ],
        ),
    ],
)
def test_calculate_card_stats(data, expected):
    df = pd.DataFrame(data, columns=["Номер карты", "Сумма платежа"])
    result = utils.calculate_card_stats(df)



# Тесты для get_top_transactions
def test_get_top_transactions():
    test_data = {
        "Дата операции": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
        "Сумма платежа": ["-1000,00", "-500,00", "-2000,00"],
        "Категория": ["Еда", "Транспорт", "Зарплата"],
        "Описание": ["Ресторан", "Такси", "ЗП"],
    }
    df = pd.DataFrame(test_data)
    result = utils.get_top_transactions(df, 3)
    assert [t["amount"] for t in result] == [-2000.00, -1000.00, -500.00]


# Тесты для загрузки переменных окружения
@patch("src.utils.load_dotenv")
@patch("src.utils.os.getenv")
def test_api_key_loading(mock_getenv, mock_load):
    mock_getenv.return_value = "test_env_key"
    utils.API_LAYER_KEY = None  # Сброс кэшированного значения
    from importlib import reload

    reload(utils)
    assert utils.API_LAYER_KEY == "test_env_key"

# Тест для fetch_stock_prices с пустым списком акций
@patch("src.utils.load_user_settings")
@patch("requests.get")
def test_fetch_stock_prices_empty_list(mock_get, mock_load_settings):
    """Тест с пустым списком акций должен возвращать пустой список"""
    mock_settings = {"alpha_vantage_api_key": "settings_key"}
    mock_load_settings.return_value = mock_settings

    result = utils.fetch_stock_prices([])
    assert result == []
    mock_get.assert_not_called()


# Тест для calculate_card_stats с пустыми данными
def test_calculate_card_stats_empty_data():
    """Тест с пустым DataFrame должен возвращать пустой список"""
    df = pd.DataFrame(columns=["Номер карты", "Сумма платежа"])
    result = utils.calculate_card_stats(df)
    assert result == []

# Тест для get_greeting с граничным значением перехода между приветствиями
@pytest.mark.parametrize(
    "hour,expected",
    [
        (11, "Доброе утро"),  # Последний час утра
        (12, "Добрый день"),  # Первый час дня
    ],
)
def test_get_greeting_boundary_values(hour, expected):
    """Тест проверяет корректность перехода между приветствиями на границах часов"""
    test_time = datetime(2023, 1, 1, hour)
    assert utils.get_greeting(test_time) == expected



def test_load_transactions_success():
    """Тест успешной загрузки файла"""
    test_data = {
        "Дата операции": ["01.01.2023 12:00:00"],
        "Сумма": [100],
        "Категория": ["Еда"]
    }

    with patch('src.utils.os.path.exists', return_value=True), \
            patch('src.utils.pd.read_excel', return_value=pd.DataFrame(test_data)):
        result = load_transactions("test.xlsx")

        assert not result.empty
        assert result["Дата операции"].dt.year[0] == 2023
        assert result["Сумма"][0] == 100


def test_file_not_found():
    """Тест случая, когда файл не существует"""
    with patch('src.utils.os.path.exists', return_value=False):
        result = load_transactions("missing.xlsx")
        assert result.empty


def test_read_error():
    """Тест ошибки при чтении файла"""
    with patch('src.utils.os.path.exists', return_value=True), \
            patch('src.utils.pd.read_excel', side_effect=Exception("Read error")):
        result = load_transactions("corrupt.xlsx")
        assert result.empty


@pytest.fixture
def sample_transactions():
    return pd.DataFrame({
        "Дата операции": [
            datetime(2023, 1, 1),
            datetime(2023, 1, 15),
            datetime(2023, 1, 31),
            datetime(2023, 2, 1)
        ],
        "Сумма": [100, 200, 300, 400]
    })


def test_filters_transactions_correctly(sample_transactions):
    """Проверяет правильность фильтрации транзакций"""
    input_date = datetime(2023, 1, 20)
    result = filter_transactions_by_date(sample_transactions, input_date)

    assert len(result) == 2
    assert all(result["Дата операции"] <= input_date)
    assert all(result["Дата операции"].dt.month == 1)


def test_handles_empty_result(sample_transactions):
    """Проверяет обработку случая без транзакций"""
    result = filter_transactions_by_date(sample_transactions, datetime(2022, 12, 1))
    assert result.empty


@patch("src.utils.logging.error")
def test_handles_errors(mock_logging):
    """Проверяет обработку ошибок"""
    invalid_df = pd.DataFrame({"Wrong_column": [1, 2]})
    result = filter_transactions_by_date(invalid_df, datetime(2023, 1, 1))

    assert result.empty
    mock_logging.assert_called_once()
    assert "Ошибка фильтрации транзакций" in mock_logging.call_args[0][0]


def test_fetch_currency_rates_success():
    """Тест успешного получения курсов валют"""
    test_currencies = ["USD", "EUR", "RUB"]
    mock_response = {
        "Valute": {
            "USD": {"Value": 75.50},
            "EUR": {"Value": 85.25}
        }
    }

    with patch('src.utils.requests.get') as mock_get:
        # Настраиваем mock-ответ
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        # Вызываем тестируемую функцию
        result = fetch_currency_rates(test_currencies)

        # Проверяем результаты
        assert len(result) == 3
        assert {"currency": "USD", "rate": 75.5} in result
        assert {"currency": "EUR", "rate": 85.25} in result
        assert {"currency": "RUB", "rate": 1.0} in result

        # Проверяем вызов API
        mock_get.assert_called_once_with(
            "https://www.cbr-xml-daily.ru/daily_json.js",
            timeout=10
        )


def test_fetch_currency_rates_missing_currency():
    """Тест обработки отсутствующей валюты"""
    test_currencies = ["GBP"]  # Валюта отсутствует в ответе
    mock_response = {"Valute": {"USD": {"Value": 75.50}}}

    with patch('src.utils.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        result = fetch_currency_rates(test_currencies)
        assert result == []  # Должен вернуть пустой список для отсутствующей валюты


@patch('src.utils.logging.error')
def test_fetch_currency_rates_error(mock_logging):
    """Тест обработки ошибки запроса"""
    test_currencies = ["USD"]

    with patch('src.utils.requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection error")

        result = fetch_currency_rates(test_currencies)
        assert result == []
        mock_logging.assert_called_once_with(
            "Ошибка получения курсов валют: Connection error"
        )