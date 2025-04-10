import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

import pandas as pd
import requests

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",
    filemode="a",
)

# Получение API ключа из переменных окружения
API_LAYER_KEY = os.getenv("API_LAYER_KEY")
if not API_LAYER_KEY:
    logging.warning("API ключ не найден в .env файле (переменная API_LAYER_KEY)")


def get_greeting(datetime_obj: datetime) -> str:
    """Возвращает приветствие в зависимости от времени суток."""
    hour = datetime_obj.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def load_user_settings() -> dict:
    """Загружает настройки пользователя из JSON-файла."""
    try:
        with open("user_settings.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки user_settings.json: {e}")
        return {}


def load_transactions(
    filename: str = r"C:\Users\spaik\PycharmProjects\BankingOperations\data\transactions.xlsx",
) -> pd.DataFrame:
    """Загружает данные транзакций из Excel."""
    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Файл {filename} не найден")

        df = pd.read_excel(filename)
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        logging.info(f"Успешно загружен файл: {filename}")
        return df
    except Exception as e:
        logging.error(f"Ошибка загрузки транзакций: {e}")
        return pd.DataFrame()


def filter_transactions_by_date(transactions_df: pd.DataFrame, input_date: datetime) -> pd.DataFrame:
    """Фильтрует транзакции с начала месяца до указанной даты."""
    try:
        start_of_month = input_date.replace(day=1)
        mask = (transactions_df["Дата операции"] >= start_of_month) & (transactions_df["Дата операции"] <= input_date)
        return transactions_df[mask]
    except Exception as e:
        logging.error(f"Ошибка фильтрации транзакций: {e}")
        return pd.DataFrame()


def calculate_card_stats(filtered_df: pd.DataFrame) -> list[dict]:
    """Вычисляет статистику по картам (сумма расходов, кешбэк)."""
    try:
        if not filtered_df.empty:
            filtered_df["last_digits"] = filtered_df["Номер карты"].str[-4:]
            filtered_df["amount"] = filtered_df["Сумма платежа"].astype(str).str.replace(",", ".").astype(float)
            expenses = filtered_df[filtered_df["amount"] < 0]
            card_groups = expenses.groupby("last_digits")["amount"].sum().reset_index()
            card_groups["total_spent"] = (-card_groups["amount"]).round(2)
            card_groups["cashback"] = (card_groups["total_spent"] / 100).round(2)
            return card_groups.to_dict("records")
        return []
    except Exception as e:
        logging.error(f"Ошибка расчета статистики карт: {e}")
        return []


def get_top_transactions(filtered_df: pd.DataFrame, n: int = 5) -> list[dict]:
    """Возвращает топ-N транзакций по сумме."""
    try:
        if not filtered_df.empty:
            df = filtered_df.copy()
            df["amount"] = df["Сумма платежа"].astype(str).str.replace(",", ".").astype(float)
            df["abs_amount"] = df["amount"].abs()
            top_trans = df.sort_values("abs_amount", ascending=False).head(n)
            top_trans["date"] = top_trans["Дата операции"].dt.strftime("%d.%m.%Y")
            return (
                top_trans[["date", "amount", "Категория", "Описание"]]
                .rename(columns={"Категория": "category", "Описание": "description"})
                .to_dict("records")
            )
        return []
    except Exception as e:
        logging.error(f"Ошибка получения топ-транзакций: {e}")
        return []


def fetch_currency_rates(currencies: list[str]) -> list[dict]:
    """Получает курсы валют через API ЦБ РФ."""
    try:
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=10)
        response.raise_for_status()
        data = response.json()
        rates = []
        for curr in currencies:
            if curr == "RUB":
                rates.append({"currency": curr, "rate": 1.0})
            elif curr in data["Valute"]:
                rate = data["Valute"][curr]["Value"]
                rates.append({"currency": curr, "rate": round(rate, 2)})
        return rates
    except Exception as e:
        logging.error(f"Ошибка получения курсов валют: {e}")
        return []


def fetch_stock_prices(stocks: list[str]) -> list[dict]:
    """Получает цены акций через Alpha Vantage API."""
    prices = []
    if not API_LAYER_KEY:
        logging.error("API ключ не доступен для получения цен акций")
        return prices

    for stock in stocks:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}&apikey={API_LAYER_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "Global Quote" in data and "05. price" in data["Global Quote"]:
                price = float(data["Global Quote"]["05. price"])
                prices.append({"stock": stock, "price": round(price, 2)})
            else:
                logging.warning(f"Не удалось получить цену для {stock}: {data}")
        except Exception as e:
            logging.error(f"Ошибка получения цены акции {stock}: {e}")
    return prices
