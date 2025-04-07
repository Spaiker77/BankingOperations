import json
from datetime import datetime, timedelta
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.reports import load_settings, load_transactions, spending_by_category


@pytest.fixture
def sample_settings():
    return {"default_currency": "RUB"}


@pytest.fixture
def sample_transactions():
    now = datetime.now()
    return pd.DataFrame(
        {
            "Дата операции": [
                (now - timedelta(days=1)).strftime("%Y-%m-%d"),
                now.strftime("%Y-%m-%d"),
            ],
            "Категория": ["Еда", "Транспорт"],
            "Сумма платежа": [1000, 500],
            "Описание": ["Обед", "Такси"],
        }
    )


def test_load_settings():
    test_data = '{"key": "value"}'
    with patch("builtins.open", mock_open(read_data=test_data)):
        result = load_settings()
        assert result == {"key": "value"}


def test_load_transactions():
    test_df = pd.DataFrame(
        {
            "Дата операции": ["2025-01-01", "2025-01-02"],
            "Категория": ["Еда", "Транспорт"],
            "Сумма платежа": [1000, 500],
            "Описание": ["Обед", "Такси"],
        }
    )
    with patch("pandas.read_excel", return_value=test_df):
        result = load_transactions()
        pd.testing.assert_frame_equal(result, test_df)


@pytest.mark.parametrize(
    "category,expected_count",
    [
        ("Еда", 1),
        ("Транспорт", 1),
        ("Несуществующая", 0),
    ],
)
def test_spending_by_category(category, expected_count, sample_settings, sample_transactions):
    with (
        patch("src.reports.load_settings", return_value=sample_settings),
        patch("src.reports.load_transactions", return_value=sample_transactions),
    ):

        result = spending_by_category(category)
        data = json.loads(result)

        assert len(data) == expected_count
        if expected_count > 0:
            assert isinstance(data[0]["date"], str)
            assert data[0]["category"] == category


def test_spending_by_category_error_handling(caplog):
    error_msg = "Test error"
    with patch("src.reports.load_settings", side_effect=Exception(error_msg)):
        result = spending_by_category("Любая")
        assert json.loads(result) == []
        assert error_msg in caplog.text
