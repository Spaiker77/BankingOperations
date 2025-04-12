import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
from src.reports import load_transactions, spending_by_category


# Фикстура для мока
@pytest.fixture
def mock_read_excel():
    with patch("src.reports.pd.read_excel") as mock:
        yield mock


# Фикстура для тестовых данных
@pytest.fixture
def sample_data():
    now = datetime.now()
    return pd.DataFrame(
        {
            "Дата операции": [now - timedelta(days=i) for i in range(10)],
            "Категория": ["Food"] * 5 + ["Transport"] * 5,
            "Сумма платежа": np.random.rand(10) * 1000,
            "Описание": ["Test"] * 10,
        }
    )


# Тесты для load_transactions
class TestLoadTransactions:
    @patch("src.reports.logger")
    def test_load_transactions_success(self, mock_logger, mock_read_excel, sample_data):
        # Arrange
        mock_read_excel.return_value = sample_data
        test_path = "test.xlsx"

        # Act
        result = load_transactions(test_path)

        # Assert
        mock_read_excel.assert_called_once_with(test_path)
        assert not result.empty
        assert result["Дата операции"].dtype == "datetime64[ns]"
        mock_logger.error.assert_not_called()

    @patch("src.reports.logger")
    @pytest.mark.parametrize("missing_col", ["Дата операции", "Категория", "Сумма платежа"])
    def test_load_missing_columns(self, mock_logger, mock_read_excel, missing_col):
        # Arrange
        data = pd.DataFrame(
            {"Дата операции": [datetime.now()], "Категория": ["Test"], "Сумма платежа": [100], "Описание": ["Test"]}
        ).drop(columns=missing_col)

        mock_read_excel.return_value = data

        # Act
        result = load_transactions("test.xlsx")

        # Assert
        assert result.empty
        mock_logger.error.assert_called()

    @patch("src.reports.logger")
    def test_load_file_not_found(self, mock_logger, mock_read_excel):
        # Arrange
        mock_read_excel.side_effect = FileNotFoundError

        # Act
        result = load_transactions("invalid.xlsx")

        # Assert
        assert result.empty
        mock_logger.error.assert_called()


# Тесты для spending_by_category
class TestSpendingByCategory:
    @pytest.mark.parametrize(
        "category, days, expected_count", [("Food", 30, 5), ("Transport", 100, 5), ("Unknown", 10, 0)]
    )
    def test_spending_by_category(self, sample_data, category, days, expected_count):
        # Arrange
        end_date = datetime.now().strftime("%Y-%m-%d")

        # Act
        result = spending_by_category(sample_data, category, end_date)

    @patch("src.reports.logger")
    def test_empty_dataframe(self, mock_logger):  # Убрали mock_read_excel
        # Arrange
        empty_df = pd.DataFrame()

        # Act
        result = spending_by_category(empty_df, "Any")  # передаем пустой DataFrame
        data = json.loads(result)

        # Assert
        assert "error" in data
        mock_logger.error.assert_called()

    def test_date_filtering(self, sample_data):  # Убрали mock_read_excel
        # Arrange
        old_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")

        # Act
        result = spending_by_category(sample_data, "Food", old_date)  # передаем sample_data
        data = json.loads(result)

        # Assert
        assert len(data) == 0


# Тесты для обработки ошибок
def test_exception_handling(sample_data):  # Убрали mock_read_excel
    # Arrange
    with patch("src.reports.spending_by_category", side_effect=Exception("Test error")) as mock_spending:
        # Act
        result = spending_by_category(sample_data, "Test")
        data = json.loads(result)
