import json
import sys
from datetime import datetime

from reports import spending_by_category
from services import simple_search

# Импорт функций из модулей
from views import generate_response


def parse_date(date_str: str) -> datetime:
    """Парсинг даты из строки"""
    try:
        return datetime.strptime(date_str.replace("_", " "), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError("Неправильный формат даты. Используйте YYYY-MM-DD_HH:MM:SS")


def main():
    # Задаем путь к файлу
    file_path = r"C:UsersspaikPycharmProjectsBankingOperationsdata"

    if len(sys.argv) < 2:
        print("Доступные команды:")
        print("1. отчет YYYY-MM-DD_HH:MM:SS")
        print("2. поиск ПОИСКОВЫЙ_ЗАПРОС")
        print("3. категория ИМЯ_КАТЕГОРИИ [дата_конца]")
        return

    command = sys.argv[1].lower()

    try:
        if command == "отчет":
            if len(sys.argv) < 3:
                raise ValueError("Не указана дата для отчета")

            date = parse_date(sys.argv[2])
            result = generate_response(date.strftime("%Y-%m-%d %H:%M:%S"), file_path)

        elif command == "поиск":
            if len(sys.argv) < 3:
                raise ValueError("Не указан поисковый запрос")

            result = simple_search(sys.argv[2])

        elif command == "категория":
            if len(sys.argv) < 3:
                raise ValueError("Не указана категория")

            category = sys.argv[2]
            end_date = parse_date(sys.argv[3]).strftime("%Y-%m-%d") if len(sys.argv) > 3 else None
            result = spending_by_category(category=category, date=end_date, file_path=file_path)

        else:
            raise ValueError("Неизвестная команда")

        print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Ошибка: {str(e)}")
        print(f"Пример использования для команды {command}:")
        if command == "отчет":
            print("отчет YYYY-MM-DD_HH:MM:SS")
        elif command == "поиск":
            print("поиск ПОИСКОВЫЙ_ЗАПРОС")
        elif command == "категория":
            print("категория ИМЯ_КАТЕГОРИИ [дата_конца_YYYY-MM-DD]")
        else:
            print("Доступные команды: отчет, поиск, категория")
        sys.exit(1)


if __name__ == "__main__":
    main()
