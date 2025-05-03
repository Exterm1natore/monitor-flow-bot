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
        raise ValueError(f"❌ When creating a new user, the chat was of type: {type(chat).__name__}")

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
    return db.query(User).get(user_id)


def find_user_by_chat(db: Session, chat: Chat) -> Optional[User]:
    """
    Найти пользователя по данным о чате.

    :param db: Сессия базы данных.
    :param chat: Чат пользователя.
    :return: Пользователь | None.
    """
    if chat is None:
        return None
    else:
        return db.query(User).filter(User.chat_id == chat.id).one_or_none()


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
    if not text.strip():
        return []

    terms = [term.strip() for term in text.strip().split() if term.strip()]
    if not terms:
        return []

    filters = []
    for term in terms:
        pattern = f"%{term}%"
        filters.append(User.first_name.ilike(pattern))
        filters.append(User.last_name.ilike(pattern))

    return db.query(User).filter(or_(*filters)).all()


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


def delete_user_by_object(db: Session, user: User, delete_chat: bool) -> bool:
    """
    Удалить запись пользователя по основному объекту.

    :param db: Сессия базы данных.
    :param user: Объект пользователя на удаление.
    :param delete_chat: Нужно ли при удалении пользователя удалять чат.
    :return: True, если запись была удалена, False если запись не существует.
    """
    if user is None:
        return False

    db.delete(user)
    db.commit()

    # Если нужно удалить чат
    if delete_chat:
        chats.delete_chat(db, user.chat_id)

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

    if user is None:
        # Чат не найден
        return False

    db.delete(user)
    db.commit()

    # Если нужно удалить чат
    if delete_chat:
        chats.delete_chat(db, user.chat_id)

    return True


def delete_user_by_chat(db: Session, chat: Chat, delete_chat: bool) -> bool:
    """
    Удалить запись пользователя по ID.

    :param db: Сессия базы данных.
    :param chat: Чат пользователя.
    :param delete_chat: Нужно ли при удалении пользователя удалять чат.
    :return: True, если запись была удалена, False если запись не найдена.
    """
    user = find_user_by_chat(db, chat)

    if user is None:
        # Чат не найден
        return False

    db.delete(user)
    db.commit()

    # Если нужно удалить чат
    if delete_chat:
        chats.delete_chat(db, user.chat_id)

    return True
