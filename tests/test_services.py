import json
import logging
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
    assert result == TEST_DATA
    mock_read_excel.assert_called_once()


@patch("src.services.pd.read_excel")
def test_load_transactions_missing_columns(mock_read_excel):
    """Тест с отсутствием обязательных колонок"""
    mock_df = MagicMock()
    mock_df.columns = ["Дата операции", "Сумма операции"]
    mock_read_excel.return_value = mock_df

    result = load_transactions()
    assert result == []
    mock_read_excel.assert_called_once()


@patch("src.services.pd.read_excel", side_effect=Exception("Read Error"))
def test_load_transactions_read_error(mock_read_excel):
    """Тест с ошибкой при чтении файла"""
    result = load_transactions()
    assert result == []
    mock_read_excel.assert_called_once()


@patch("src.services.pd.read_excel")
def test_load_transactions_empty_df(mock_read_excel):
    """Тест с пустым DataFrame"""
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
    mock_df.fillna.return_value.astype.return_value.to_dict.return_value = []
    mock_read_excel.return_value = mock_df

    result = load_transactions()
    assert result == []
    mock_read_excel.assert_called_once()


#  Тесты для simple_search
def test_search_by_description():
    """Поиск по описанию операции"""
    result = simple_search("магазине", TEST_DATA)
    assert len(json.loads(result)) == 1
    assert json.loads(result)[0]["Описание"] == "Покупка в магазине"


def test_search_by_category():
    """Поиск по категории"""
    result = simple_search("Супермаркеты", TEST_DATA)
    assert len(json.loads(result)) == 1
    assert json.loads(result)[0]["Категория"] == "Супермаркеты"


# Параметризованные тесты
@pytest.mark.parametrize(
    "query,expected_count,expected_field,expected_value",
    [
        ("магазине", 1, "Описание", "Покупка в магазине"),
        ("Супермаркеты", 1, "Категория", "Супермаркеты"),
        ("Оплата", 1, "Описание", "Оплата интернета"),
        ("999", 0, None, None),
        (None, 0, None, None),
        ("", 0, None, None),
    ],
)
def test_search_parametrized(query, expected_count, expected_field, expected_value):
    """Разные варианты поиска"""
    result = simple_search(query, TEST_DATA)
    assert len(json.loads(result)) == expected_count
    if expected_count > 0 and expected_field:
        assert json.loads(result)[0][expected_field] == expected_value


# Тест обработки ошибок
def test_search_with_empty_data():
    """Тест с пустыми данными"""
    result = simple_search("test", [])
    assert result == json.dumps([])


def test_search_invalid_transactions():
    """Тест с неверным типом transactions"""
    result = simple_search("test", "not a list")
    assert result == json.dumps([])
