import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение API ключа
API_LAYER_KEY = os.getenv("API_LAYER_KEY")
if not API_LAYER_KEY:
    logger.warning("API ключ не найден в .env файле")


def load_transactions(file_path: str) -> pd.DataFrame:
    """Загружает транзакции из указанного файла"""
    try:
        df = pd.read_excel(file_path)

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


def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> str:
    """Анализ трат по категории"""
    try:
        # Определение периода
        end_date = pd.to_datetime(date) if date else datetime.now()
        start_date = end_date - timedelta(days=90)

        if transactions.empty:
            logger.error("Нет данных для анализа")  # Добавлено логирование
            return json.dumps({"error": "Нет данных для анализа"})

        # Фильтрация данных
        filtered = transactions[
            (transactions["Категория"].str.lower() == category.lower())
            & (transactions["Дата операции"].between(start_date, end_date))
        ]

        # Формирование результата
        result = filtered[["Дата операции", "Категория", "Сумма платежа", "Описание"]]
        return result.to_json(orient="records", force_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return json.dumps({"error": str(e)})
