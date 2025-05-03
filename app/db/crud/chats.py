from sqlalchemy.orm import Session
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
        raise ValueError(f"❌ When creating a new Chat, the chat_type was of type: {type(chat_type).__name__}")
    # Если тип чата объект
    elif isinstance(chat_type, ChatType):
        id_chat_type = chat_type.id
    # Если тип чата индекс или название
    elif isinstance(chat_type, int) or isinstance(chat_type, str):
        id_chat_type = chat_types.find_chat_type(db, chat_type).id
    else:
        raise TypeError(f"❌ chat_type must be of type ChatType, int or str, received: {type(chat_type).__name__}")

    chat = Chat(email=email, chat_type=id_chat_type)
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
    if isinstance(identifier, int):
        chat = db.query(Chat).get(identifier)
    elif isinstance(identifier, str):
        chat = db.query(Chat).filter(Chat.email == identifier).one_or_none()
    else:
        raise TypeError(f"❌ Identifier must be of type int or str, received: {type(identifier).__name__}")

    return chat


def delete_chat(db: Session, identifier: Union[int, str]) -> bool:
    """
    Удалить запись чата.

    :param db: Сессия базы данных.
    :param identifier: Идентификатор чата (int - ID чата, str - email чата).
    :return: True, если запись была удалена, False если запись не найдена.
    """
    chat = find_chat(db, identifier)

    if chat is None:
        # Чат не найден
        return False

    db.delete(chat)
    db.commit()
    return True
