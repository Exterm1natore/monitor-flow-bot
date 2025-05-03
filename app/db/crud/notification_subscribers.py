from sqlalchemy.orm import Session
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
        raise ValueError("❌ When adding a new notifications subscriber, the notification_type was of type: "
                         f"{type(notification_type).__name__}")

    notification_subscriber = NotificationSubscriber(chat_id=chat.id, notification_type=notification_type.id,
                                                     granted_by=authorizer_id, granted_at=granted_at)

    db.add(notification_subscriber)
    db.commit()
    db.refresh(notification_subscriber)
    return notification_subscriber


def find_notifications_subscriber_by_chat(db: Session,
                                          chat: Chat,
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
        return list()

    # join для соединения с таблицей Chat
    query = db.query(NotificationSubscriber).join(Chat, Chat.id == NotificationSubscriber.chat_id)

    # Фильтрация по конкретному чату
    query = query.filter(NotificationSubscriber.chat_id == chat.id)

    # Опциональная фильтрация по типу уведомления
    if notification_type:
        query = query.filter(NotificationSubscriber.notification_type == notification_type.id)

    return query.all()


def find_notification_subscribers_by_granted_by(db: Session, granted_by: str) -> List[NotificationSubscriber]:
    """
    Найти список подписок на уведомления по данным предоставившего доступ.

    :param db: Сессия базы данных.
    :param granted_by: Email пользователя, предоставившего доступ.
    :return: Список найденных подписок на уведомления.
    """
    return db.query(NotificationSubscriber).filter(NotificationSubscriber.granted_by == granted_by).all()


def find_notification_subscribers_by_type(db: Session, notification_type: NotificationType) -> List[NotificationSubscriber]:
    """
    Найти список подписок на уведомления по типу уведомления.

    :param db: Сессия базы данных.
    :param notification_type: Тип уведомления.
    :return: Список найденных подписок на уведомления.
    """
    return db.query(NotificationSubscriber).filter(
        NotificationSubscriber.notification_type == notification_type.id
    ).all()


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
    # Преобразуем date в datetime, если нужно
    if isinstance(date_or_start, date) and not isinstance(date_or_start, datetime):
        start_dt = datetime.combine(date_or_start, datetime.min.time())
    else:
        start_dt = date_or_start

    if end:
        if isinstance(end, date) and not isinstance(end, datetime):
            end_dt = datetime.combine(end, datetime.max.time())
        else:
            end_dt = end
        query = db.query(NotificationSubscriber).filter(
            NotificationSubscriber.granted_at.between(start_dt, end_dt)
        )
    else:
        # Если end не указан, ищем по дате: весь день
        day_end = start_dt + timedelta(days=1)
        query = db.query(NotificationSubscriber).filter(
            NotificationSubscriber.granted_at >= start_dt,
            NotificationSubscriber.granted_at < day_end
        )

    return query.all()


def delete_notifications_subscriber_by_basic_model(db: Session, notification_subscriber: NotificationSubscriber) -> bool:
    """
    Удалить запись подписчика уведомлений по базовому объекту.

    :param db: Сессия базы данных.
    :param notification_subscriber: Базовый объект слушателя.
    :return: True, если запись была удалена, False если запись не существует.
    """
    if notification_subscriber is None:
        return False

    db.delete(notification_subscriber)
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
    # Если тип уведомления не был найден
    if notification_type is None:
        raise ValueError("❌ When deleting a notifications subscriber, the notification_type was of type: "
                         f"{type(notification_type).__name__}")

    subscriber = find_notifications_subscriber_by_chat(db, chat, notification_type)

    if not subscriber:
        return False
    # Если записей больше 1 ошибка
    elif len(subscriber) > 1:
        raise RuntimeError("❌ Expected 0 or 1 subscriber, found "
                           f"{len(subscriber)} for chat ID {chat.id} and notification type ID {notification_type.id}")

    db.delete(subscriber[0])
    db.commit()
    return True
