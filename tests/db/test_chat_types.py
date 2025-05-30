import pytest
from sqlalchemy.orm import Session
from app.db.models import ChatType
from app.db import crud


@pytest.fixture
def chat_type(session: Session) -> ChatType:
    chat_type = ChatType(type="private")
    session.add(chat_type)
    session.commit()
    return chat_type


def test_find_chat_type_by_id(session: Session, chat_type: ChatType):
    result = crud.find_chat_type(session, chat_type.id)
    assert result is not None
    assert result.id == chat_type.id
    assert result.type == "private"


def test_find_chat_type_by_type(session: Session, chat_type: ChatType):
    result = crud.find_chat_type(session, "private")
    assert result is not None
    assert result.id == chat_type.id
    assert result.type == "private"


def test_find_chat_type_not_found(session: Session):
    result_by_id = crud.find_chat_type(session, 999)
    result_by_type = crud.find_chat_type(session, "nonexistent")
    assert result_by_id is None
    assert result_by_type is None


def test_find_chat_type_invalid_type(session: Session):
    with pytest.raises(TypeError) as exc_info:
        crud.find_chat_type(session, 3.14)

    assert "Invalid identifier type" in str(exc_info.value)
