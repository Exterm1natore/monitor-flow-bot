from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.db.models import Administrator, User


def create_administrator(db: Session, user: User, authorizer_id: str, granted_at: datetime) -> Administrator:
    """
    Добавить пользователя в администраторы.

    :param db: Сессия базы данных.
    :param user: Пользователь, которому предоставляется доступ.
    :param authorizer_id: Кем предоставлен доступ.
    :param granted_at: Время назначения.
    :return: Объект Administrator.
    """
    if user is None:
        raise ValueError("❌ The user has not been transferred.")

    admin = Administrator(user_id=user.id, granted_by=authorizer_id, granted_at=granted_at)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def find_administrator_by_user(db: Session, user: User) -> Optional[Administrator]:
    """
    Получить запись администратора по объекту пользователя.

    :param db: Сессия базы данных.
    :param user: Объект пользователя.
    :return: Объект Administrator или None.
    """
    if user is None:
        return None

    return db.query(Administrator).filter_by(user_id=user.id).one_or_none()


def is_user_administrator(db: Session, user: User) -> bool:
    """
    Проверить, является ли пользователь администратором.

    :param db: Сессия базы данных.
    :param user: Объект пользователя.
    :return: True, если администратор, иначе False.
    """
    if user is None:
        raise TypeError("❌ The user object has not been transferred.")

    return db.query(db.query(Administrator).filter_by(user_id=user.id).exists()).scalar()


def delete_administrator(db: Session, admin: Administrator) -> bool:
    """
    Удалить запись администратора по основному объекту.

    :param db: Сессия базы данных.
    :param admin: Объект администратора на удаление.
    :return: True, если запись была удалена, False если запись не существует.
    """
    if admin is None:
        return False

    db.delete(admin)
    db.commit()
    return True


def delete_administrator_by_user(db: Session, user: User) -> bool:
    """
    Удалить запись администратора по данным пользователя.

    :param db: Сессия базы данных.
    :param user: Пользователь.
    :return: True, если запись была удалена, False если запись не найдена.
    """
    admin = find_administrator_by_user(db, user)
    return delete_administrator(db, admin)
