from unittest.mock import patch
from datetime import datetime
import pytest
from src.main import parse_date, main
import  json


def test_parse_date_success():
    """Тест успешного парсинга даты"""
    test_cases = [
        ("2023-01-15_12:30:45", datetime(2023, 1, 15, 12, 30, 45)),
        ("2023-01-15 12:30:45", datetime(2023, 1, 15, 12, 30, 45)),  # Проверка замены _ на пробел
    ]

    for date_str, expected in test_cases:
        result = parse_date(date_str)
        assert result == expected


def test_parse_date_invalid_format():
    """Тест неправильного формата даты"""
    invalid_cases = [
        "2023-01-15",  # Нет времени
        "15-01-2023_12:30:45",  # Неправильный порядок даты
        "invalid_date",  # Полностью неверный формат
    ]

    for date_str in invalid_cases:
        with pytest.raises(ValueError) as exc_info:
            parse_date(date_str)
        assert "Неправильный формат даты" in str(exc_info.value)


@patch("src.main.datetime")
def test_datetime_strptime_called_correctly(mock_datetime):
    """Тест что strptime вызывается с правильными параметрами"""
    test_str = "2023-01-15_12:30:45"

    # Настраиваем mock
    mock_datetime.strptime.return_value = datetime(2023, 1, 15, 12, 30, 45)

    result = parse_date(test_str)

    # Проверяем что strptime вызывался с правильными аргументами
    mock_datetime.strptime.assert_called_once_with("2023-01-15 12:30:45", "%Y-%m-%d %H:%M:%S")
    assert result == datetime(2023, 1, 15, 12, 30, 45)


@patch('src.main.sys.argv')
@patch('src.main.print')
def test_main_scenarios(mock_print, mock_argv):
    """Параметризованный тест основных сценариев"""
    test_cases = [
        # Без аргументов - вывод справки
        (
            ['script.py'],
            ["Доступные команды:", "отчет", "поиск", "категория"],
            None
        ),
        # Ошибки в командах
        (
            ['script.py', 'отчет'],
            ["Ошибка: Не указана дата для отчета"],
            1
        ),
        (
            ['script.py', 'поиск'],
            ["Ошибка: Не указан поисковый запрос"],
            1
        ),
        (
            ['script.py', 'категория'],
            ["Ошибка: Не указана категория"],
            1
        ),
        (
            ['script.py', 'неизвестная'],
            ["Ошибка: Неизвестная команда"],
            1
        )
    ]




@patch('src.main.sys.argv', ['script.py', 'отчет', '2023-01-01_00:00:00'])
@patch('src.main.generate_response')
@patch('src.main.print')
def test_report_command(mock_print, mock_generate):
    """Тест успешной команды отчет"""
    mock_generate.return_value = '{"data": "test"}'
    main()
    mock_print.assert_called_once_with(json.dumps({"data": "test"}, indent=2, ensure_ascii=False))


@patch('src.main.sys.argv', ['script.py', 'поиск', 'запрос'])
@patch('src.main.simple_search')
@patch('src.main.print')
def test_search_command(mock_print, mock_search):
    """Тест успешной команды поиск"""
    mock_search.return_value = '{"result": "ok"}'
    main()
    mock_print.assert_called_once_with(json.dumps({"result": "ok"}, indent=2, ensure_ascii=False))
