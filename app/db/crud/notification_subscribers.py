from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime
from app.db.models import NotificationSubscriber, Chat, NotificationType


def add_notification_subscriber(db: Session,
                                chat: Chat,
                                notification_type: NotificationType,
                                authorizer_id: str, granted_at: datetime
                                ) -> NotificationSubscriber:
    """
    Добавить подписчика на определённый тип уведомлений.

    :param db: Сессия базы данных.
    :param chat: Чат, который становится подписчиком уведомлений.
    :param notification_type: Тип уведомлений, на который подписывается чат.
    :param authorizer_id: Кем предоставлен доступ.
    :param granted_at: Время предоставления.
    :return: Добавленная запись.
    """
    # Если тип уведомления не был найден
    if notification_type is None:
        raise ValueError(f"❌ notification_type is required, got {type(notification_type).__name__}")

    subscriber = NotificationSubscriber(
        chat_id=chat.id,
        notification_type=notification_type.id,
        granted_by=authorizer_id,
        granted_at=granted_at
    )

    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber


def delete_notifications_subscriber(db: Session, subscriber: Optional[NotificationSubscriber]) -> bool:
    """
    Удалить запись подписчика уведомлений по базовому объекту.

    :param db: Сессия базы данных.
    :param subscriber: Базовый объект слушателя.
    :return: True, если запись была удалена, False если запись не существует.
    """
    if subscriber is None:
        return False

    db.delete(subscriber)
    db.commit()
    return True


def delete_notification_subscriber_by_data(db: Session, chat: Optional[Chat], notification_type: NotificationType) -> bool:
    """
    Удалить запись подписчика уведомлений по данным чата и типу уведомлений.

    :param db: Сессия базы данных.
    :param chat: Чат, по которому идёт фильтрация.
    :param notification_type: Тип уведомлений, по которому идёт фильтрация.
    :return: True, если запись была удалена, False если запись не существует.
    """
    if notification_type is None:
        raise ValueError(f"❌ notification_type is required, got {type(notification_type).__name__}")

    if chat is None:
        return False

    stmt = select(NotificationSubscriber).where(
        and_(
            NotificationSubscriber.chat_id == chat.id,
            NotificationSubscriber.notification_type == notification_type.id
        )
    )

    subscriber: Optional[NotificationSubscriber] = db.execute(stmt).scalars().one_or_none()

    if not subscriber:
        return False

    return delete_notifications_subscriber(db, subscriber)
