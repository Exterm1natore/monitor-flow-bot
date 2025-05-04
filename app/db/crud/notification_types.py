from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import NotificationType
from typing import Optional, Union


def find_notification_type(db: Session, identifier: Union[int, str]) -> Optional[NotificationType]:
    """
    Найти тип уведомления по идентификатору.

    :param db: Сессия базы данных.
    :param identifier: Идентификатор типа уведомления (int - ID типа уведомления, str - название типа уведомления).
    :return: Тип уведомления | None.
    """
    stmt = None

    if isinstance(identifier, int):
        stmt = select(NotificationType).where(NotificationType.id == identifier)
    elif isinstance(identifier, str):
        stmt = select(NotificationType).where(NotificationType.type == identifier)
    else:
        raise TypeError(f"❌ Identifier must be of type int or str, received: {type(identifier).__name__}")

    return db.execute(stmt).scalar_one_or_none()
