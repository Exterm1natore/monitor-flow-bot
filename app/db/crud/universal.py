from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select
from sqlalchemy import func
from typing import List, Type, TypeVar, Optional

# Базовый тип ORM моделей
BaseModel = declarative_base()
T = TypeVar("T", bound=BaseModel)


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


def count_records(db: Session, model: Type[T]) -> int:
    """
    Возвращает количество записей в заданной таблице.

    :param db: Активная сессия SQLAlchemy.
    :param model: Класс ORM-модели таблицы.
    :return: Количество записей.
    """
    stmt = select(func.count()).select_from(model)
    return db.execute(stmt).scalar_one()
