from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.db.models import Chat, User
from typing import Optional, List
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


def find_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Найти пользователя по его ID.

    :param db: Сессия базы данных.
    :param user_id: ID пользователя.
    :return: Пользователь | None.
    """
    return db.get(User, user_id)


def find_user_by_chat(db: Session, chat: Chat) -> Optional[User]:
    """
    Найти пользователя по данным о чате.

    :param db: Сессия базы данных.
    :param chat: Чат пользователя.
    :return: Пользователь | None.
    """
    if chat is None:
        return None

    return db.query(User).filter_by(chat_id=chat.id).one_or_none()


def find_users_by_name(db: Session, first_name: Optional[str] = None, last_name: Optional[str] = None) -> List[User]:
    """
    Поиск пользователей по частичному совпадению имени и/или фамилии.

    :param db: Сессия базы данных.
    :param first_name: Имя или его часть (опционально).
    :param last_name: Фамилия или её часть (опционально).
    :return: Список найденных пользователей.
    """
    query = db.query(User)
    filters = []

    if first_name:
        filters.append(User.first_name.ilike(f"%{first_name}%"))
    if last_name:
        filters.append(User.last_name.ilike(f"%{last_name}%"))

    if filters:
        query = query.filter(and_(*filters))

    return query.all()


def find_users_by_text_name(db: Session, text: str) -> List[User]:
    """
    Найти пользователей по содержимому строки (имя и/или фамилия).

    :param db: Сессия базы данных.
    :param text: Строка с фрагментами имени и/или фамилии.
    :return: Список подходящих пользователей.
    """
    text = text.strip()
    if not text:
        return []

    terms = [term for term in text.split() if term]
    if not terms:
        return []

    filters = [
        or_(
            User.first_name.ilike(f"%{term}%"),
            User.last_name.ilike(f"%{term}%")
        ) for term in terms
    ]

    return db.query(User).filter(and_(*filters)).all()


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


def delete_user(db: Session, user: User, delete_chat: bool) -> bool:
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


def delete_user_by_id(db: Session, user_id: int, delete_chat: bool) -> bool:
    """
    Удалить запись пользователя по ID.

    :param db: Сессия базы данных.
    :param user_id: ID пользователя.
    :param delete_chat: Нужно ли при удалении пользователя удалять чат.
    :return: True, если запись была удалена, False если запись не найдена.
    """
    user = find_user_by_id(db, user_id)
    return delete_user(db, user, delete_chat)


def delete_user_by_chat(db: Session, chat: Chat, delete_chat: bool) -> bool:
    """
    Удалить запись пользователя по ID.

    :param db: Сессия базы данных.
    :param chat: Чат пользователя.
    :param delete_chat: Нужно ли при удалении пользователя удалять чат.
    :return: True, если запись была удалена, False если запись не найдена.
    """
    user = find_user_by_chat(db, chat)
    return delete_user(db, user, delete_chat)
