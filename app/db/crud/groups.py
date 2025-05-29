from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import Chat, Group
from . import chats


def create_group(db: Session, chat: Chat, title: str) -> Group:
    """
    Создать новую группу.

    :param db: Сессия базы данных.
    :param chat: Чат группы.
    :param title: Наименование группы.
    :return: Новая группа.
    """
    if chat is None:
        raise ValueError("❌ Chat must not be None when creating a group")

    group = Group(chat_id=chat.id, title=title)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, group: Group, title: Optional[str] = None) -> Group:
    """
    Обновить данные группы.

    :param db: Сессия базы данных.
    :param group: Объект группы, которую нужно обновить.
    :param title: Новое название (опционально).
    :return: Обновлённый объект.
    """
    if title is not None:
        group.title = title

    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group: Optional[Group], delete_chat: bool) -> bool:
    """
    Удалить запись группы по основному объекту.

    :param db: Сессия базы данных.
    :param group: Объект группы на удаление.
    :param delete_chat: Нужно ли при удалении группы удалять чат.
    :return: True, если запись была удалена, False если запись не существует.
    """
    if group is None:
        return False

    db.delete(group)
    db.commit()

    # Если нужно удалить чат
    if delete_chat:
        chats.delete_chat_by_data(db, group.chat_id)

    return True
