import pytest
from datetime import datetime
from app import db


@pytest.fixture
def test_user(session):
    chat_type = db.ChatType(type="private")
    chat = db.Chat(email="test_admin@example.com", chat_type_model=chat_type)
    user = db.User(first_name="Admin", last_name="User", chat=chat)
    session.add_all([chat_type, chat, user])
    session.commit()
    return user


def test_create_administrator(session, test_user):
    granted_at = datetime.utcnow()
    admin = db.crud.create_administrator(session, test_user, "system", granted_at)

    assert isinstance(admin, db.Administrator)
    assert admin.user_id == test_user.id
    assert admin.granted_by == "system"
    assert admin.granted_at == granted_at


def test_create_administrator_invalid_user(session):
    with pytest.raises(ValueError, match="user has not been transferred"):
        db.crud.create_administrator(session, None, "system", datetime.utcnow())


def test_delete_administrator(session, test_user):
    admin = db.crud.create_administrator(session, test_user, "system", datetime.utcnow())
    deleted = db.crud.delete_administrator(session, admin)

    assert deleted is True
    assert db.crud.find_one_record(session, db.Administrator, {db.Administrator.user_id: test_user.id}) is None


def test_delete_administrator_none(session):
    assert db.crud.delete_administrator(session, None) is False
