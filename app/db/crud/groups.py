from typing import Optional, List
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
        raise ValueError(f"❌ When creating a new group, the chat was of type: {type(chat).__name__}")

    group = Group(chat_id=chat.id, title=title)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def find_group_by_id(db: Session, group_id: int) -> Optional[Group]:
    """
    Найти группу по её ID.

    :param db: Сессия базы данных.
    :param group_id: ID группы.
    :return: Группа | None.
    """
    return db.query(Group).get(group_id)


def find_group_by_chat(db: Session, chat: Chat) -> Optional[Group]:
    """
    Найти группу по данным о чате.

    :param db: Сессия базы данных.
    :param chat: Чат группы.
    :return: Группа | None.
    """
    if chat is None:
        return None
    else:
        return db.query(Group).filter(Group.chat_id == chat.id).one_or_none()


def find_groups_by_title(db: Session, query: str, exact_match: bool = False) -> List[Group]:
    """
    Найти группы по части или полному совпадению заголовка.

    :param db: Сессия базы данных.
    :param query: Текст для поиска по заголовку.
    :param exact_match: Если True — ищется точное совпадение, иначе — частичное.
    :return: Список подходящих групп.
    """
    if not query.strip():
        return []

    query = query.strip()

    if exact_match:
        # Точное совпадение, нечувствительное к регистру (сравниваем в нижнем регистре)
        return db.query(Group).filter(Group.title.ilike(query)).all()
    else:
        # Частичное совпадение
        pattern = f"%{query}%"
        return db.query(Group).filter(Group.title.ilike(pattern)).all()


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


def delete_group_by_object(db: Session, group: Group, delete_chat: bool) -> bool:
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
        chats.delete_chat(db, group.chat_id)

    return True


def delete_group_by_id(db: Session, group_id: int, delete_chat: bool) -> bool:
    """
    Удалить запись группы по ID.

    :param db: Сессия базы данных.
    :param group_id: ID группы.
    :param delete_chat: Нужно ли при удалении группы удалять чат.
    :return: True, если запись была удалена, False если запись не найдена.
    """
    group = find_group_by_id(db, group_id)

    if group is None:
        # Чат не найден
        return False

    db.delete(group)
    db.commit()

    # Если нужно удалить чат
    if delete_chat:
        chats.delete_chat(db, group.chat_id)

    return True


def delete_group_by_chat(db: Session, chat: Chat, delete_chat: bool):
    """
    Удалить запись группы по данным чата.

    :param db: Сессия базы данных.
    :param chat: Чат группы.
    :param delete_chat: Нужно ли при удалении группы удалять и чат.
    :return: True, если запись была удалена, False если запись не найдена.
    """
    group = find_group_by_chat(db, chat)

    if group is None:
        # Группа не найдена
        return False

    db.delete(group)
    db.commit()

    # Если нужно удалить чат
    if delete_chat:
        chats.delete_chat(db, group.chat_id)

    return True
