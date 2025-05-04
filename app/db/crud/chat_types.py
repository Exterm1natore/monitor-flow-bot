from sqlalchemy.orm import Session
from sqlalchemy import select
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
        stmt = select(ChatType).where(ChatType.id == identifier)
    elif isinstance(identifier, str):
        stmt = select(ChatType).where(ChatType.type == identifier)
    else:
        raise TypeError(f"❌ Invalid identifier type: expected int or str, received: {type(identifier).__name__}")

    result = db.execute(stmt).scalar_one_or_none()
    return result
