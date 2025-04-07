import json
from unittest.mock import MagicMock, patch

import pytest

from src.services import load_transactions, simple_search

TEST_DATA = [
    {
        "Дата операции": "01.01.2023",
        "Описание": "Покупка в магазине",
        "Категория": "Супермаркеты",
        "Сумма операции": "1000",
        "Валюта операции": "RUB",
        "MCC": "5411",
    },
    {
        "Дата операции": "02.01.2023",
        "Описание": "Оплата интернета",
        "Категория": "Связь",
        "Сумма операции": "500",
        "Валюта операции": "RUB",
        "MCC": "4814",
    },
]


# Тесты для load_transactions
@patch("src.services.pd.read_excel")
def test_load_transactions_success(mock_read_excel):
    """Тест успешной загрузки данных с правильными колонками"""
    mock_df = MagicMock()
    mock_df.columns = [
        "Дата операции",
        "Описание",
        "Категория",
        "Сумма операции",
        "Валюта операции",
        "MCC",
        "Дата платежа",
        "Статус",
    ]
    mock_df.fillna.return_value.astype.return_value.to_dict.return_value = TEST_DATA
    mock_read_excel.return_value = mock_df

    result = load_transactions()
    assert len(result) == 2
    assert "Категория" in result[0]
    assert "Описание" in result[1]


@patch("src.services.pd.read_excel")
def test_load_transactions_missing_columns(mock_read_excel):
    """Тест с отсутствием обязательных колонок"""
    mock_df = MagicMock()
    mock_df.columns = ["Дата операции", "Сумма операции"]
    mock_read_excel.return_value = mock_df

    result = load_transactions()
    assert result == []


#  Тесты для simple_search
@patch("src.services.load_transactions")
def test_search_by_description(mock_load):
    """Поиск по описанию операции"""
    mock_load.return_value = TEST_DATA
    result = json.loads(simple_search("магазине"))
    assert len(result) == 1
    assert result[0]["Описание"] == "Покупка в магазине"


@patch("src.services.load_transactions")
def test_search_by_category(mock_load):
    """Поиск по категории"""
    mock_load.return_value = TEST_DATA
    result = json.loads(simple_search("Супермаркеты"))
    assert len(result) == 1
    assert result[0]["Категория"] == "Супермаркеты"


# Параметризованные тесты
@pytest.mark.parametrize(
    "query,expected_count,expected_field,expected_value",
    [
        ("магазине", 1, "Описание", "Покупка в магазине"),
        ("Супермаркеты", 1, "Категория", "Супермаркеты"),
        ("Оплата", 1, "Описание", "Оплата интернета"),
        ("999", 0, None, None),
    ],
)
@patch("src.services.load_transactions")
def test_search_parametrized(mock_load, query, expected_count, expected_field, expected_value):
    """Разные варианты поиска"""
    mock_load.return_value = TEST_DATA
    result = json.loads(simple_search(query))
    assert len(result) == expected_count
    if expected_count > 0 and expected_field:
        assert result[0][expected_field] == expected_value


# Тест обработки ошибок
@patch("src.services.load_transactions")
def test_search_with_empty_data(mock_load):
    """Тест с пустыми данными"""
    mock_load.return_value = []
    assert simple_search("test") == json.dumps([])
