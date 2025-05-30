import pytest
from sqlalchemy.orm import Session
from app.db.models import ChatType
from app.db import crud


@pytest.fixture
def chat_type(session: Session) -> ChatType:
    ct = ChatType(type="group")
    session.add(ct)
    session.commit()
    return ct


@pytest.fixture
def chat(session: Session, chat_type: ChatType):
    return crud.create_chat(session, email="groupchat@example.com", chat_type=chat_type)


def test_create_group(session: Session, chat):
    group = crud.create_group(session, chat, title="My Group")
    assert group.id is not None
    assert group.title == "My Group"
    assert group.chat_id == chat.id
    assert group.chat.email == chat.email


def test_create_group_with_none_chat(session: Session):
    with pytest.raises(ValueError):
        crud.create_group(session, None, "Should Fail")


def test_update_group_title(session: Session, chat):
    group = crud.create_group(session, chat, "Old Title")
    updated = crud.update_group(session, group, title="New Title")
    assert updated.id == group.id
    assert updated.title == "New Title"


def test_update_group_title_none(session: Session, chat):
    group = crud.create_group(session, chat, "Title")
    updated = crud.update_group(session, group)  # No change
    assert updated.title == "Title"


def test_delete_group_only(session: Session, chat):
    group = crud.create_group(session, chat, "To Delete")
    deleted = crud.delete_group(session, group, delete_chat=False)
    assert deleted
    # Chat should still exist
    assert crud.find_chat(session, chat.id) is not None


def test_delete_group_and_chat(session: Session, chat):
    group = crud.create_group(session, chat, "To Delete All")
    deleted = crud.delete_group(session, group, delete_chat=True)
    assert deleted
    # Chat should be deleted
    assert crud.find_chat(session, chat.id) is None


def test_delete_group_none(session: Session):
    assert crud.delete_group(session, None, delete_chat=True) is False
