from sqlalchemy.orm import Session
from contextlib import contextmanager
from .database import SessionLocal

# Добавление моделей в базу данных
from . import models
Base = models.Base


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
