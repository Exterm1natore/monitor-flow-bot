import pytest
from sqlalchemy.orm import Session
from app.db.models import NotificationType, ChatType
from app.db import crud
from datetime import datetime


@pytest.fixture
def chat_type(session: Session):
    ct = ChatType(type="notification")
    session.add(ct)
    session.commit()
    return ct


@pytest.fixture
def chat(session: Session, chat_type):
    return crud.create_chat(session, "unsub@example.com", chat_type=chat_type)


@pytest.fixture
def notification_types(session: Session):
    types = [
        NotificationType(type="alpha", description="Alpha"),
        NotificationType(type="beta", description="Beta"),
        NotificationType(type="gamma", description="Gamma"),
    ]
    session.add_all(types)
    session.commit()
    return types


def test_find_notification_type_by_id(session: Session, notification_types):
    target = notification_types[0]
    result = crud.find_notification_type(session, target.id)
    assert result is not None
    assert result.id == target.id
    assert result.type == target.type


def test_find_notification_type_by_type(session: Session, notification_types):
    target = notification_types[1]
    result = crud.find_notification_type(session, target.type)
    assert result is not None
    assert result.id == target.id


def test_find_notification_type_invalid_type(session: Session):
    with pytest.raises(TypeError):
        crud.find_notification_type(session, 3.14)  # float — недопустимый тип


def test_find_notification_type_not_found(session: Session):
    result = crud.find_notification_type(session, "non-existent-type")
    assert result is None


def test_find_unsubscribed_notification_types(session: Session, chat, notification_types):
    # Подписываемся только на один тип уведомлений
    subscribed = notification_types[0]
    crud.add_notification_subscriber(
        db=session,
        chat=chat,
        notification_type=subscribed,
        authorizer_id="tester",
        granted_at=datetime.utcnow()
    )

    result = crud.find_unsubscribed_notification_types(session, chat)

    # Остальные два типа должны вернуться как неподписанные
    unsubscribed_types = [nt.type for nt in result]
    assert len(result) == 2
    assert subscribed.type not in unsubscribed_types
    assert all(nt in ["beta", "gamma"] for nt in unsubscribed_types)


def test_find_unsubscribed_notification_types_none_chat(session: Session):
    with pytest.raises(ValueError):
        crud.find_unsubscribed_notification_types(session, None)


def test_find_unsubscribed_notification_types_all(session: Session, chat, notification_types):
    # Никакие подписки не создаём — должны вернуть все типы
    result = crud.find_unsubscribed_notification_types(session, chat)
    assert len(result) == len(notification_types)
