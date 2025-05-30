import re
import pytest
from datetime import datetime
import pytz
from app.utils.date_and_time import (
    get_current_date_moscow,
    get_current_date_with_format,
    format_datetime
)


def test_get_current_date_moscow_timezone():
    dt = get_current_date_moscow()
    assert dt.tzinfo is not None
    r = dt.tzinfo.zone
    assert dt.tzinfo.zone == 'Europe/Moscow'


def test_get_current_date_with_format_default():
    formatted = get_current_date_with_format()
    assert isinstance(formatted, str)
    # Проверка на соответствие шаблону dd.mm.yyyy HH:MM
    assert re.match(r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}', formatted)


def test_get_current_date_with_format_custom():
    fmt = "%Y-%m-%d"
    formatted = get_current_date_with_format(fmt)
    assert re.match(r'\d{4}-\d{2}-\d{2}', formatted)


@pytest.mark.parametrize("dt,expected_prefix", [
    (None, datetime.utcnow().strftime('%Y-%m-%d')),
    ("2023-01-01T12:00:00Z", "2023-01-01"),
    (int(datetime(2022, 5, 5, 15, 0).timestamp()), "2022-05-05"),
    (datetime(2020, 4, 10, 12, 30), "2020-04-10")
])
def test_format_datetime_basic(dt, expected_prefix):
    formatted = format_datetime(dt, fmt="%Y-%m-%d %H:%M:%S")
    assert formatted.startswith(expected_prefix)


def test_format_datetime_with_timezone_conversion():
    dt = "2023-01-01T12:00:00Z"
    formatted = format_datetime(dt, tz="Europe/Moscow", to_local=True, fmt="%H:%M")
    # Москва зимой UTC+3, ожидаем 15:00
    assert formatted.startswith("15:")


def test_format_datetime_invalid_string():
    with pytest.raises(ValueError):
        format_datetime("not-a-date")


def test_format_datetime_string_parse_disabled():
    with pytest.raises(ValueError):
        format_datetime("2023-01-01", parse_string=False)


def test_format_datetime_unknown_timezone():
    with pytest.raises(ValueError):
        format_datetime(datetime.utcnow(), tz="Invalid/Zone", to_local=True)


def test_format_datetime_unix_timestamp():
    ts = int(datetime(2021, 1, 1, 12, 0).timestamp())
    formatted = format_datetime(ts, fmt="%Y-%m-%d %H:%M:%S")
    assert formatted.startswith("2021-01-01")


def test_format_datetime_timezone_preserved():
    tz = pytz.timezone("Europe/Moscow")
    dt = tz.localize(datetime(2022, 12, 12, 10, 0))
    formatted = format_datetime(dt, fmt="%Y-%m-%d %H:%M")
    assert formatted.startswith("2022-12-12 10:")