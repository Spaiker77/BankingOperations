import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)  # Исправлено: Используем __name__

# Получение API ключа из переменных окружения
API_LAYER_KEY = os.getenv("API_LAYER_KEY")
if not API_LAYER_KEY:
    logger.warning("API ключ не найден в .env файле (переменная API_LAYER_KEY)")

# Путь к Excel-файлу
EXCEL_PATH = Path("C:/Users/spaik/PycharmProjects/BankingOperations/data/transactions.xlsx")


def load_transactions() -> List[Dict[str, Any]]:
    """Загружает транзакции из Excel файла"""
    try:
        df = pd.read_excel(EXCEL_PATH)

        # Проверка обязательных колонок
        required_columns = ["Описание", "Категория"]
        if not all(col in df.columns for col in required_columns):
            logger.error("Отсутствуют необходимые колонки в Excel")
            return []

        # Преобразование в список словарей
        return df.fillna("").astype(str).to_dict("records")

    except FileNotFoundError:
        logger.error(f"Файл не найден: {EXCEL_PATH}")
        return []
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {str(e)}")
        return []


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> str:
    """
    Простой поиск транзакций по описанию или категории.
    Принимает строку запроса и список транзакций.
    Возвращает JSON-ответ с результатами.
    """
    try:
        # Валидация запроса
        if not isinstance(query, str) or not query.strip():
            logger.warning("Получен пустой или некорректный запрос")
            return json.dumps([])

        # Валидация транзакций
        if not isinstance(transactions, list):
            logger.error("Транзакции должны быть представлены в виде списка.")
            return json.dumps([])

        # Нормализация запроса
        query_clean = query.strip().lower()

        # Функциональный поиск
        result = [
            t
            for t in transactions
            if (query_clean in t.get("Описание", "").lower() or query_clean in t.get("Категория", "").lower())
        ]

        logger.info(f"Найдено совпадений: {len(result)}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        return json.dumps([])
