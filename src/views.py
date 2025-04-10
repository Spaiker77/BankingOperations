import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from dotenv import load_dotenv

from src.utils import (
    calculate_card_stats,
    fetch_currency_rates,
    fetch_stock_prices,
    filter_transactions_by_date,
    get_greeting,
    get_top_transactions,
    load_transactions,
    load_user_settings,
)

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение API ключа из переменных окружения
API_LAYER_KEY = os.getenv("API_LAYER_KEY")
if not API_LAYER_KEY:
    print("Warning: API_LAYER_KEY not found in .env file")


def generate_response(input_data: str) -> str:
    """
    Генерирует JSON-ответ для главной страницы.
    Принимает строку в формате "YYYY-MM-DD HH:MM:SS,path/to/file.xlsx".
    Если путь к файлу не указан, используем значение по умолчанию "data.xlsx".
    """
    try:
        # Разделяем строку на дату/время и путь к файлу
        parts = input_data.split(",")
        input_datetime_str = parts[0]
        file_path = parts[1] if len(parts) > 1 else "data.xlsx"  # Значение по умолчанию

        input_datetime = datetime.strptime(input_datetime_str, "%Y-%m-%d %H:%M:%S")
        greeting = get_greeting(input_datetime)

        settings = load_user_settings()
        currencies = settings.get("user_currencies", [])
        stocks = settings.get("user_stocks", [])

        transactions_df = load_transactions(file_path)
        filtered_df = filter_transactions_by_date(transactions_df, input_datetime)

        cards_data = calculate_card_stats(filtered_df)
        top_trans = get_top_transactions(filtered_df)
        currency_rates = fetch_currency_rates(currencies)
        stock_prices = fetch_stock_prices(stocks, API_LAYER_KEY)  # Используем ключ из .env

        response_data: Dict[str, Any] = {
            "greeting": greeting,
            "cards": cards_data,
            "top_transactions": top_trans,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }

        return json.dumps(response_data, ensure_ascii=False, indent=2)

    except Exception as e:
        error_response = {"error": "Internal Server Error", "message": str(e)}
        return json.dumps(error_response, ensure_ascii=False, indent=2)
