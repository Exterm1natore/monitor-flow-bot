from sqlalchemy.orm import Session
from app.db.models import ChatType
from typing import Optional, Union


def find_chat_type(db: Session, identifier: Union[int, str]) -> Optional[ChatType]:
    """
    Найти тип чата по идентификатору.

    :param db: Сессия базы данных.
    :param identifier: Идентификатор типа чата (int - ID типа чата, str - название типа чата).
    :return: Тип чата | None.
    """
    if isinstance(identifier, int):
        chat_type = db.query(ChatType).get(identifier)
    elif isinstance(identifier, str):
        chat_type = db.query(ChatType).filter(ChatType.type == identifier).first()
    else:
        raise TypeError(f"❌ Identifier must be of type int or str, received: {type(identifier).__name__}")

    return chat_type
