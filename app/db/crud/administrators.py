from typing import Optional
from sqlalchemy.orm import Session
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


def delete_administrator(db: Session, admin: Optional[Administrator]) -> bool:
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
