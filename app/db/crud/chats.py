from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Chat, ChatType
from . import chat_types
from typing import Optional, Union


def create_chat(db: Session, email: str, chat_type: Union[ChatType, int, str]) -> Chat:
    """
    Создать новый чат.

    :param db: Сессия базы данных.
    :param email: Адрес чата.
    :param chat_type: Тип чата.
    :return: Новый чат.
    """
    # Если тип чата не был найден
    if chat_type is None:
        raise ValueError(f"❌ chat_type is None (expected ChatType, int or str)")

    if isinstance(chat_type, ChatType):
        chat_type_id = chat_type.id
    elif isinstance(chat_type, (int, str)):
        found = chat_types.find_chat_type(db, chat_type)
        if not found:
            raise ValueError(f"❌ ChatType not found for identifier: {chat_type}")
        chat_type_id = found.id
    else:
        raise TypeError(f"❌ chat_type must be ChatType, int, or str — received {type(chat_type).__name__}")

    chat = Chat(email=email, chat_type=chat_type_id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def find_chat(db: Session, identifier: Union[int, str]) -> Optional[Chat]:
    """
    Найти чат по идентификатору.

    :param db: Сессия базы данных.
    :param identifier: Идентификатор чата (int - ID чата, str - email чата).
    :return: Чат | None.
    """
    stmt = None
    if isinstance(identifier, int):
        stmt = select(Chat).where(Chat.id == identifier)
    elif isinstance(identifier, str):
        stmt = select(Chat).where(Chat.email == identifier)
    else:
        raise TypeError(f"❌ Identifier must be int or str, received {type(identifier).__name__}")

    return db.execute(stmt).scalar_one_or_none()


def delete_chat(db: Session, chat: Optional[Chat]) -> bool:
    """
    Удалить чат по основному объекту.

    :param db: Сессия базы данных.
    :param chat: Объект чата на удаление.
    :return: True, если запись была удалена, False если запись не существует.
    """
    if chat is None:
        return False

    db.delete(chat)
    db.commit()
    return True


def delete_chat_by_data(db: Session, identifier: Union[int, str]) -> bool:
    """
    Удалить запись чата.

    :param db: Сессия базы данных.
    :param identifier: Идентификатор чата (int - ID чата, str - email чата).
    :return: True, если запись была удалена, False если запись не найдена.
    """
    chat = find_chat(db, identifier)
    return delete_chat(db, chat)
