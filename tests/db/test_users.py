import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch
from app.db.models import ChatType, User
from app.db import crud


@pytest.fixture
def chat_type(session: Session) -> ChatType:
    ct = ChatType(type="private")
    session.add(ct)
    session.commit()
    return ct


@pytest.fixture
def chat(session: Session, chat_type: ChatType):
    return crud.create_chat(session, email="userchat@example.com", chat_type=chat_type)


@pytest.fixture
def user(session: Session, chat) -> User:
    user = User(chat_id=chat.id, first_name="Иватин", last_name="Kashpo")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# --- create_user ---

def test_create_user_success(session: Session, chat):
    user = crud.create_user(session, chat, "Иван", "Старый")
    assert isinstance(user, User)
    assert user.chat_id == chat.id
    assert user.first_name == "Иван"
    assert user.last_name == "Старый"


def test_create_user_without_lastname(session: Session, chat):
    user = crud.create_user(session, chat, "Lomonosov")
    assert user.last_name is None


def test_create_user_no_chat(session: Session):
    with pytest.raises(ValueError, match="Chat must not be None"):
        crud.create_user(session, None, "Вано")


# --- update_user ---

def test_update_user_first_name(session: Session, user: User):
    updated = crud.update_user(session, user, first_name="Updated")
    assert updated.first_name == "Updated"
    assert updated.last_name == "Kashpo"


def test_update_user_last_name(session: Session, user: User):
    updated = crud.update_user(session, user, last_name="UpdatedLast")
    assert updated.last_name == "UpdatedLast"
    assert updated.first_name == "Иватин"


def test_update_user_both_names(session: Session, user: User):
    updated = crud.update_user(session, user, first_name="Иван", last_name="Иванович")
    assert updated.first_name == "Иван"
    assert updated.last_name == "Иванович"


def test_update_user_no_changes(session: Session, user: User):
    updated = crud.update_user(session, user)
    assert updated.first_name == user.first_name
    assert updated.last_name == user.last_name


# --- delete_user ---

def test_delete_user_success(session: Session, user: User):
    deleted = crud.delete_user(session, user, delete_chat=False)
    assert deleted is True
    assert session.get(User, user.id) is None


@patch("app.db.crud.chats.delete_chat_by_data")
def test_delete_user_with_chat(mock_delete_chat, session: Session, user: User):
    deleted = crud.delete_user(session, user, delete_chat=True)
    assert deleted is True
    mock_delete_chat.assert_called_once_with(session, user.chat_id)


def test_delete_user_none(session: Session):
    deleted = crud.delete_user(session, None, delete_chat=True)
    assert deleted is False
