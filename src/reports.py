import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути к файлам
PROJECT_ROOT = Path(__file__).parent.parent
EXCEL_PATH = PROJECT_ROOT / "data" / "transactions.xlsx"
SETTINGS_PATH = PROJECT_ROOT / "user_settings.json"


def load_settings() -> dict:
    """Загружает настройки из JSON-файла"""
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек: {str(e)}")
        return {}


def load_transactions() -> pd.DataFrame:
    """Загружает транзакции из Excel-файла"""
    try:
        df = pd.read_excel(EXCEL_PATH)

        # Проверка обязательных колонок
        required_columns = ["Дата операции", "Категория", "Сумма платежа"]
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            logger.error(f"Отсутствуют колонки: {missing}")
            return pd.DataFrame()

        # Конвертация даты
        df["Дата операции"] = pd.to_datetime(df["Дата операции"])
        return df

    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {str(e)}")
        return pd.DataFrame()


def spending_by_category(category: str, date: Optional[str] = None) -> str:
    """
    Возвращает траты по категории за последние 3 месяца в формате JSON

    """
    try:
        # Загрузка данных и настроек
        transactions = load_transactions()

        # Определяем дату отсчета
        end_date = pd.to_datetime(date) if date else datetime.now()
        start_date = end_date - timedelta(days=90)

        if transactions.empty:
            logger.error("Нет данных для анализа")
            return json.dumps([])

        # Фильтрация данных
        filtered = transactions[
            (transactions["Категория"].str.lower() == category.lower())
            & (transactions["Дата операции"].between(start_date, end_date))
        ]

        logger.info(f"Найдено записей: {len(filtered)}")

        # Формирование результата
        result = filtered[["Дата операции", "Категория", "Сумма платежа", "Описание"]].to_dict(orient="records")

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка формирования отчета: {str(e)}")
        return json.dumps([])
