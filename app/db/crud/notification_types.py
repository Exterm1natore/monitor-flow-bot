from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import NotificationType, Chat, NotificationSubscriber
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


def find_unsubscribed_notification_types(db: Session, chat: Chat) -> List[NotificationType]:
    """
    Найти список типов уведомлений, на которые чат не подписан.

    :param db: Сессия базы данных.
    :param chat: Чат, для которого ищутся неподписанные типы уведомлений.
    :return: Список типов уведомлений, на которые чат не подписан.
    """
    if chat is None:
        return []

    # Под-запрос для получения всех ID типов, на которые чат уже подписан
    subquery = select(NotificationSubscriber.notification_type).where(NotificationSubscriber.chat_id == chat.id).subquery()

    # Основной запрос: все NotificationType, которых нет в подписках
    stmt = select(NotificationType).where(NotificationType.id.not_in(select(subquery)))

    return db.execute(stmt).scalars().all()
