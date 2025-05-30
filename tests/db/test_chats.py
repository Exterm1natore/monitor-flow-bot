import pytest
from sqlalchemy.orm import Session
from app.db.models import ChatType
from app.db import crud


@pytest.fixture
def chat_type(session: Session) -> ChatType:
    obj = ChatType(type="group")
    session.add(obj)
    session.commit()
    return obj


def test_create_chat_with_model(session: Session, chat_type: ChatType):
    chat = crud.create_chat(session, "test@example.com", chat_type)
    assert chat.id is not None
    assert chat.email == "test@example.com"
    assert chat.chat_type == chat_type.id
    assert chat.chat_type_model.type == "group"


def test_create_chat_with_id(session: Session, chat_type: ChatType):
    chat = crud.create_chat(session, "byid@example.com", chat_type.id)
    assert chat.email == "byid@example.com"
    assert chat.chat_type_model.type == "group"


def test_create_chat_with_type_str(session: Session, chat_type: ChatType):
    chat = crud.create_chat(session, "byname@example.com", "group")
    assert chat.email == "byname@example.com"
    assert chat.chat_type_model.id == chat_type.id


def test_create_chat_with_invalid_type(session: Session):
    with pytest.raises(TypeError):
        crud.create_chat(session, "fail@example.com", 3.14)


def test_create_chat_with_none(session: Session):
    with pytest.raises(ValueError):
        crud.create_chat(session, "none@example.com", None)


def test_create_chat_with_unresolved_type(session: Session):
    with pytest.raises(ValueError):
        crud.create_chat(session, "bad@example.com", "nonexistent")


def test_find_chat_by_id(session: Session, chat_type: ChatType):
    chat = crud.create_chat(session, "findbyid@example.com", chat_type)
    found = crud.find_chat(session, chat.id)
    assert found is not None
    assert found.email == "findbyid@example.com"


def test_find_chat_by_email(session: Session, chat_type: ChatType):
    chat = crud.create_chat(session, "findbymail@example.com", chat_type)
    found = crud.find_chat(session, "findbymail@example.com")
    assert found is not None
    assert found.id == chat.id


def test_find_chat_invalid_identifier(session: Session):
    with pytest.raises(TypeError):
        crud.find_chat(session, {"invalid": True})


def test_delete_chat(session: Session, chat_type: ChatType):
    chat = crud.create_chat(session, "todelete@example.com", chat_type)
    deleted = crud.delete_chat(session, chat)
    assert deleted
    assert crud.find_chat(session, chat.id) is None


def test_delete_chat_none(session: Session):
    assert crud.delete_chat(session, None) is False


def test_delete_chat_by_data_with_id(session: Session, chat_type: ChatType):
    chat = crud.create_chat(session, "delbyid@example.com", chat_type)
    result = crud.delete_chat_by_data(session, chat.id)
    assert result
    assert crud.find_chat(session, chat.id) is None


def test_delete_chat_by_data_with_email(session: Session, chat_type: ChatType):
    chat = crud.create_chat(session, "delbyemail@example.com", chat_type)
    result = crud.delete_chat_by_data(session, "delbyemail@example.com")
    assert result
    assert crud.find_chat(session, chat.id) is None


def test_delete_chat_by_data_not_found(session: Session):
    assert crud.delete_chat_by_data(session, "missing@example.com") is False
    assert crud.delete_chat_by_data(session, 99999) is False
