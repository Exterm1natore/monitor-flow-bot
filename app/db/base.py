from typing import Type, TypeVar, List
from sqlalchemy.orm import Session, declarative_base
from contextlib import contextmanager
from .database import SessionLocal
from sqlalchemy.ext.declarative import DeclarativeMeta

# Добавление моделей в базу данных
from . import models
Base = models.Base

# Базовый тип ORM моделей
T = TypeVar("T", bound=declarative_base())


def enable_foreign_keys(session: Session):
    """
    Включить поддержку внешних ключей для каждой сессии.

    :param session: Текущая сессия.
    """
    session.execute('PRAGMA foreign_keys = ON;')


@contextmanager
def get_db_session(enable_foreign_key: bool = True):
    """
    Получить сессию работы с базой данных.

    :param enable_foreign_key: Включить ли проверку внешних ключей.
    :return: Экземпляр сессии SQLAlchemy.
    """
    db = SessionLocal()
    try:
        if enable_foreign_key:
            enable_foreign_keys(db)

        yield db
    finally:
        db.close()


def get_tablename_by_model(model: Type[T]):
    """
    Получить название таблицы по типу модели.

    :param model: ORM-модель.
    :return: Название таблицы.
    """
    if hasattr(model, "__table__"):
        return model.__table__.name
    raise TypeError(f"{model} is not a valid SQLAlchemy model class")


def get_model_by_tablename(table_name: str) -> Type[DeclarativeMeta]:
    """
    Найти ORM‑класс по имени таблицы.

    Поддерживает SQLAlchemy 1.x и 2.x.
    """
    # 2.x: Registry → mappers
    try:
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            if getattr(cls, "__tablename__", None) == table_name:
                return cls
    except AttributeError:
        # fallback для 1.x
        for cls in Base._decl_class_registry.values():
            if isinstance(cls, type) and getattr(cls, "__tablename__", None) == table_name:
                return cls

    raise ValueError(f"Model with table '{table_name}' is not registered in Base")


def get_table_columns(table_name: str):
    """
    Возвращает объект Table.columns по имени таблицы из метаданных Base.

    :param table_name: Имя таблицы.
    :return: sqlalchemy.sql.base.ImmutableColumnCollection (словарь колонок).
    """
    table = Base.metadata.tables.get(table_name)
    if table is None:
        raise ValueError(f"Model with table '{table_name}' is not registered in Base")
    return table.columns


def get_all_tables_names() -> List[str]:
    """
    Получить название всех таблиц базы данных.

    :return: Список названий всех таблиц.
    """
    return list(Base.metadata.tables.keys())


def model_exists_by_table_name(table_name: str) -> bool:
    """
    Проверяет, существует ли модель, привязанная к таблице с указанным именем.

    :param table_name: Имя таблицы для проверки.
    :return: True, если таблица с таким названием существует, иначе False.
    """
    for mapper in Base.registry.mappers:
        if mapper.class_.__table__.name == table_name:
            return True
    return False
