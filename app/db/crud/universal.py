from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import func
from typing import List, Type


def get_all_records(db: Session, model: Type[DeclarativeMeta]) -> List:
    """
    Получить все записи из таблицы модели.

    :param db: Текущая сессия базы данных.
    :param model: SQLAlchemy-модель таблицы.
    :return: Список записей (объекты модели).
    """
    return db.query(model).all()


def count_records(db: Session, model: Type) -> int:
    """
    Возвращает количество записей в заданной таблице.

    :param db: Активная сессия SQLAlchemy.
    :param model: Класс ORM-модели таблицы.
    :return: Количество записей.
    """
    return db.query(func.count()).select_from(model).scalar()
