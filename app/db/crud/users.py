from sqlalchemy.orm import Session
from app.db.models import Chat, User
from typing import Optional
from . import chats


def create_user(db: Session, chat: Chat, first_name: str, last_name: Optional[str] = None) -> User:
    """
    Создать нового пользователя.

    :param db: Сессия базы данных.
    :param chat: Чат пользователя.
    :param first_name: Имя пользователя.
    :param last_name: Фамилия пользователя.
    :return: Новый пользователь.
    """
    if chat is None:
        raise ValueError("❌ Chat must not be None when creating a user")

    user = User(chat_id=chat.id, first_name=first_name, last_name=last_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
    """
    Обновить данные пользователя.

    :param db: Сессия базы данных.
    :param user: Объект пользователя, которого нужно обновить.
    :param first_name: Новое имя (опционально).
    :param last_name: Новая фамилия (опционально).
    :return: Обновлённый объект.
    """
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: Optional[User], delete_chat: bool) -> bool:
    """
    Удалить запись пользователя по основному объекту.

    :param db: Сессия базы данных.
    :param user: Объект пользователя на удаление.
    :param delete_chat: Нужно ли при удалении пользователя удалять чат.
    :return: True, если запись была удалена, False если запись не существует.
    """
    if not user:
        return False

    db.delete(user)
    db.commit()

    if delete_chat:
        chats.delete_chat_by_data(db, user.chat_id)

    return True
