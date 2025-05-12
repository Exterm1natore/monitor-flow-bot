from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import Optional, List, Union
from datetime import datetime, date, timedelta
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


def find_notifications_subscriber_by_chat(db: Session,
                                          chat: Optional[Chat],
                                          notification_type: Optional[NotificationType] = None
                                          ) -> List[NotificationSubscriber]:
    """
    Найти список подписок на уведомления для заданного чата.

    :param db: Сессия базы данных.
    :param chat: Чат, по которому идёт поиск подписок на уведомления.
    :param notification_type: Дополнительная фильтрация по типу уведомления.
    :return: Список найденных подписок на уведомления.
    """
    if chat is None:
        return []

    stmt = select(NotificationSubscriber).where(NotificationSubscriber.chat_id == chat.id)

    if notification_type:
        stmt = stmt.where(NotificationSubscriber.notification_type == notification_type.id)

    return db.execute(stmt).scalars().all()


def find_notification_subscribers_by_granted_by(db: Session, granted_by: str) -> List[NotificationSubscriber]:
    """
    Найти список подписок на уведомления по данным предоставившего доступ.

    :param db: Сессия базы данных.
    :param granted_by: Email пользователя, предоставившего доступ.
    :return: Список найденных подписок на уведомления.
    """
    stmt = select(NotificationSubscriber).where(NotificationSubscriber.granted_by == granted_by)
    return db.execute(stmt).scalars().all()


def find_notification_subscribers_by_type(db: Session, notification_type: NotificationType) -> List[NotificationSubscriber]:
    """
    Найти список подписок на уведомления по типу уведомления.

    :param db: Сессия базы данных.
    :param notification_type: Тип уведомления.
    :return: Список найденных подписок на уведомления.
    """
    stmt = select(NotificationSubscriber).where(NotificationSubscriber.notification_type == notification_type.id)
    return db.execute(stmt).scalars().all()


def find_notification_subscribers_by_date(db: Session,
                                          date_or_start: Union[date, datetime],
                                          end: Optional[Union[date, datetime]] = None
                                          ) -> List[NotificationSubscriber]:
    """
    Найти список подписок на уведомления по дате или в промежутке времени.

    :param db: Сессия базы данных.
    :param date_or_start: Дата (для одного дня) или начало диапазона.
    :param end: Конец диапазона, если нужен период.
    :return: Список найденных подписок на уведомления.
    """
    start_dt = (
        datetime.combine(date_or_start, datetime.min.time())
        if isinstance(date_or_start, date) and not isinstance(date_or_start, datetime)
        else date_or_start
    )

    if end:
        end_dt = (
            datetime.combine(end, datetime.max.time())
            if isinstance(end, date) and not isinstance(end, datetime)
            else end
        )
        stmt = select(NotificationSubscriber).where(
            NotificationSubscriber.granted_at.between(start_dt, end_dt)
        )
    else:
        stmt = select(NotificationSubscriber).where(
            and_(
                NotificationSubscriber.granted_at >= start_dt,
                NotificationSubscriber.granted_at < start_dt + timedelta(days=1)
            )
        )

    return db.execute(stmt).scalars().all()


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


def delete_notification_subscriber_by_data(db: Session, chat: Chat, notification_type: NotificationType) -> bool:
    """
    Удалить запись подписчика уведомлений по данным чата и типу уведомлений.

    :param db: Сессия базы данных.
    :param chat: Чат, по которому идёт фильтрация.
    :param notification_type: Тип уведомлений, по которому идёт фильтрация.
    :return: True, если запись была удалена, False если запись не существует.
    """
    if notification_type is None:
        raise ValueError(f"❌ notification_type is required, got {type(notification_type).__name__}")

    subscribers = find_notifications_subscriber_by_chat(db, chat, notification_type)

    if not subscribers:
        return False
    elif len(subscribers) > 1:
        raise RuntimeError(
            f"❌ Expected 0 or 1 subscriber, found {len(subscribers)} "
            f"for chat ID {chat.id} and notification type ID {notification_type.id}"
        )

    return delete_notifications_subscriber(db, subscribers[0])
