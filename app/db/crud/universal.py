from typing import List, Type, Optional, Union, Any, Dict
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, func, String, Text, DateTime, and_
from app.db.base import T
from datetime import datetime
import dateutil.parser


def _build_condition(
    model: Type[T],
    field: Union[str, InstrumentedAttribute],
    value: Any,
    partial_match: bool = False
):
    """
    Формирует SQLAlchemy-условие для одного поля модели.

    Поддерживает:
    - partial_match=True для String/Text и Datetime (по дате).
    - Точное сравнение для всех типов.

    :param model: ORM-модель.
    :param field: Название или атрибут поля.
    :param value: Значение.
    :param partial_match: Для строк — LIKE, для datetime — по дате.
    :return: Сформированное условие.
    """
    # получаем InstrumentedAttribute
    if isinstance(field, InstrumentedAttribute):
        col = field
    else:
        try:
            col = getattr(model, field)
        except AttributeError:
            raise AttributeError(f"Model '{model.__name__}' has no attribute '{field}'")

    # тип колонки
    col_type = col.property.columns[0].type
    is_string = isinstance(col_type, (String, Text))
    is_datetime = isinstance(col_type, DateTime)

    # Строка для LIKE
    if is_string and partial_match and isinstance(value, str):
        return col.like(f"%{value}%")

    # Частичный поиск по дате
    if is_datetime and partial_match:
        if isinstance(value, str):
            try:
                value_dt = dateutil.parser.parse(value)
            except (ValueError, TypeError):
                # Если ошибка, не преобразуем к datetime
                return col == value
        elif isinstance(value, datetime):
            value_dt = value
        else:
            raise TypeError(f"Unsupported type for datetime partial match: {type(value)}")
        # Сравнение только по дате без учёта времени
        return func.date(col) == value_dt.date()

    # Строгое сравнение
    return col == value


def get_all_records(db: Session, model: Type[T]) -> List[T]:
    """
    Получить все записи из таблицы модели.

    :param db: Текущая сессия базы данных.
    :param model: SQLAlchemy-модель таблицы.
    :return: Список записей (объекты модели).
    """
    stmt = select(model)
    return db.execute(stmt).scalars().all()


def get_records_range(
    db: Session,
    model: Type[T],
    *,
    start: Optional[int] = None,
    end:   Optional[int] = None,
    order_by: Optional[ColumnElement] = None
) -> List[T]:
    """
    Получить записи модели в диапазоне по их порядковым номерам (1‑based).

    Если ни start, ни end не заданы — вернёт все записи.
    Если задан только end — вернёт записи с 1 до end.
    Если задан только start — вернёт записи с start до конца.
    Если заданы оба — вернёт записи с start до end включительно.

    Если order_by не передан, попытаемся упорядочить по первичному ключу,
    а при его отсутствии — без явного порядка (зависит от СУБД).

    :param db: Сессия SQLAlchemy.
    :param model: Класс ORM‑модели.
    :param start: Номер первой записи (1‑based). Если None — с первой.
    :param end:   Номер последней записи (1‑based, включительно). Если None — до последней.
    :param order_by: Выражение для ORDER BY (например, model.created_at.desc()).
    :return: Список объектов модели в указанном диапазоне.
    """
    stmt = select(model)

    # Определяем порядок
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    else:
        # если у модели есть первичный ключ, используем его
        pks = list(model.__table__.primary_key.columns)
        if pks:
            stmt = stmt.order_by(*pks)

    # Преобразуем 1-based в offset / limit
    offset = 0
    limit = None

    if start is not None:
        if start < 1:
            raise ValueError("start must be >= 1")
        offset = start - 1

    if end is not None:
        if end < 1:
            raise ValueError("end must be >= 1")
        # Вычисляем кол‑во записей
        if start is not None:
            if end < start:
                return []
            limit = end - start + 1
        else:
            # только end: с 1 до end
            limit = end

    # Применяем offset и limit
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)

    return db.execute(stmt).scalars().all()


def find_one_record(
    db: Session,
    model: Type[T],
    conditions: Dict[Union[str, InstrumentedAttribute], Any],
    *,
    partial_match: bool = False
) -> Optional[T]:
    """
    Найти строго одну запись по набору условий (AND).
    Если ни одной — None, если > 1 — исключение MultipleResultsFound.

    :param db: Сессия SQLAlchemy.
    :param model: ORM-класс.
    :param conditions: Словарь {поле: значение, …}.
    :param partial_match: Строковые поля искать LIKE '%value%' вместо =.
    :return: Экземпляр модели или None.
    :raises MultipleResultsFound: Найдено больше одной записи.
    """
    if not conditions:
        raise ValueError("At least one condition must be provided")

    conds = [
        _build_condition(model, fld, val, partial_match)
        for fld, val in conditions.items()
    ]
    stmt = select(model).where(and_(*conds))
    return db.execute(stmt).scalars().one_or_none()


def find_records(
    db: Session,
    model: Type[T],
    conditions: Dict[Union[str, InstrumentedAttribute], Any],
    *,
    partial_match: bool = False
) -> List[T]:
    """
    Найти список записей по набору условий (AND).

    :param db: Сессия SQLAlchemy.
    :param model: ORM-класс.
    :param conditions: Словарь {поле: значение, …}.
    :param partial_match: Строковые поля искать LIKE '%value%' вместо =.
    :return: Список экземпляров модели.
    """
    # если нет условий — вернуть всё
    if not conditions:
        stmt = select(model)
    else:
        conds = [
            _build_condition(model, fld, val, partial_match)
            for fld, val in conditions.items()
        ]
        stmt = select(model).where(and_(*conds))

    return db.execute(stmt).scalars().all()


def count_records(db: Session, model: Type[T]) -> int:
    """
    Возвращает количество записей в заданной таблице.

    :param db: Активная сессия SQLAlchemy.
    :param model: Класс ORM-модели таблицы.
    :return: Количество записей.
    """
    stmt = select(func.count()).select_from(model)
    return db.execute(stmt).scalar_one()
