from typing import List, Type, Optional, Union, Any
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, func, String, Text
from app.db.base import T


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


def find_records(
        db: Session,
        model: Type[T],
        filter_field: Union[str, InstrumentedAttribute],
        filter_value: Any,
        *,
        partial_match: bool = False
) -> List[T]:
    """
    Найти записи в таблице по заданному условию.

    Для **строковых** полей (String, Text) можно выполнить частичный поиск.
    Для всех остальных типов — точное совпадение.

    :param db: Сессия SQLAlchemy.
    :param model: ORM-модель поиска.
    :param filter_field: Имя или атрибут поля.
    :param filter_value: Значение для фильтрации.
    :param partial_match:
        - True: для строковых полей частичный поиск.
        - False: всегда точное совпадение.
    :return: Список объектов модели, удовлетворяющих условию.
    :raises AttributeError: В модели нет такого поля.
    """
    # 1. Разрешаем строку в InstrumentedAttribute
    if isinstance(filter_field, InstrumentedAttribute):
        column_attr = filter_field
    else:
        try:
            column_attr = getattr(model, filter_field)
        except AttributeError:
            raise AttributeError(f"Model '{model.__name__}' has no attribute '{filter_field}'")

    # 2. Решаем, какой оператор использовать
    col_type = getattr(column_attr.property.columns[0], "type", None)
    is_string = isinstance(col_type, (String, Text))

    if partial_match and is_string and isinstance(filter_value, str):
        # Частичный поиск для строковых колонок
        condition = column_attr.like(f"%{filter_value}%")

    else:
        # Точное совпадение для остальных случаев
        condition = column_attr == filter_value

    # 3. Собираем и выполняем запрос
    stmt = select(model).where(condition)
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
