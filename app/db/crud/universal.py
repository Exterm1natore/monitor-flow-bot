from sqlalchemy.orm import Session, declarative_base
from sqlalchemy import select
from sqlalchemy import func
from typing import List, Type, TypeVar

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


def count_records(db: Session, model: Type[T]) -> int:
    """
    Возвращает количество записей в заданной таблице.

    :param db: Активная сессия SQLAlchemy.
    :param model: Класс ORM-модели таблицы.
    :return: Количество записей.
    """
    stmt = select(func.count()).select_from(model)
    return db.execute(stmt).scalar_one()
