import json
from datetime import datetime
from typing import Any, Dict

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


def generate_response(input_datetime_str: str, file_path: str = None) -> str:
    """
    Генерирует JSON-ответ для главной страницы.

    """
    try:
        input_datetime = datetime.strptime(input_datetime_str, "%Y-%m-%d %H:%M:%S")
        greeting = get_greeting(input_datetime)

        settings = load_user_settings()
        currencies = settings.get("user_currencies", [])
        stocks = settings.get("user_stocks", [])
        api_key = settings.get("alpha_vantage_api_key", "demo")

        transactions_df = load_transactions(file_path)
        filtered_df = filter_transactions_by_date(transactions_df, input_datetime)

        cards_data = calculate_card_stats(filtered_df)
        top_trans = get_top_transactions(filtered_df)
        currency_rates = fetch_currency_rates(currencies)
        stock_prices = fetch_stock_prices(stocks, api_key)

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
