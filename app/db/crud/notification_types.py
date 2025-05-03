from sqlalchemy.orm import Session
from app.db.models import NotificationType
from typing import Optional, Union


def find_notification_type(db: Session, identifier: Union[int, str]) -> Optional[NotificationType]:
    """
    Найти тип уведомления по идентификатору.

    :param db: Сессия базы данных.
    :param identifier: Идентификатор типа уведомления (int - ID типа уведомления, str - название типа уведомления).
    :return: Тип уведомления | None.
    """
    if isinstance(identifier, int):
        notification_type = db.query(NotificationType).get(identifier)
    elif isinstance(identifier, str):
        notification_type = db.query(NotificationType).filter(NotificationType.type == identifier).first()
    else:
        raise TypeError(f"❌ Identifier must be of type int or str, received: {type(identifier).__name__}")

    return notification_type
