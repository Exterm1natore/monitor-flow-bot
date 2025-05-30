import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import ChatType, NotificationType
from app.db import crud


@pytest.fixture
def chat_type(session: Session) -> ChatType:
    ct = ChatType(type="private")
    session.add(ct)
    session.commit()
    return ct


@pytest.fixture
def chat(session: Session, chat_type: ChatType):
    return crud.create_chat(session, email="notif@example.com", chat_type=chat_type)


@pytest.fixture
def notification_type(session: Session) -> NotificationType:
    nt = NotificationType(type="test", description="Test type")
    session.add(nt)
    session.commit()
    return nt


def test_add_notification_subscriber(session: Session, chat, notification_type):
    subscriber = crud.add_notification_subscriber(
        db=session,
        chat=chat,
        notification_type=notification_type,
        authorizer_id="admin",
        granted_at=datetime.utcnow()
    )

    assert subscriber.id is not None
    assert subscriber.chat_id == chat.id
    assert subscriber.notification_type == notification_type.id
    assert subscriber.granted_by == "admin"


def test_add_notification_subscriber_invalid_type(session: Session, chat):
    with pytest.raises(ValueError):
        crud.add_notification_subscriber(
            db=session,
            chat=chat,
            notification_type=None,
            authorizer_id="admin",
            granted_at=datetime.utcnow()
        )


def test_delete_notification_subscriber(session: Session, chat, notification_type):
    subscriber = crud.add_notification_subscriber(
        db=session,
        chat=chat,
        notification_type=notification_type,
        authorizer_id="admin",
        granted_at=datetime.utcnow()
    )

    deleted = crud.delete_notifications_subscriber(session, subscriber)
    assert deleted


def test_delete_notification_subscriber_none(session: Session):
    deleted = crud.delete_notifications_subscriber(session, None)
    assert not deleted


def test_delete_by_data_success(session: Session, chat, notification_type):
    crud.add_notification_subscriber(
        db=session,
        chat=chat,
        notification_type=notification_type,
        authorizer_id="admin",
        granted_at=datetime.utcnow()
    )

    deleted = crud.delete_notification_subscriber_by_data(
        db=session,
        chat=chat,
        notification_type=notification_type
    )
    assert deleted


def test_delete_by_data_no_record(session: Session, chat, notification_type):
    deleted = crud.delete_notification_subscriber_by_data(
        db=session,
        chat=chat,
        notification_type=notification_type
    )
    assert not deleted


def test_delete_by_data_missing_chat(session: Session, notification_type):
    deleted = crud.delete_notification_subscriber_by_data(
        db=session,
        chat=None,
        notification_type=notification_type
    )
    assert not deleted


def test_delete_by_data_missing_type(session: Session, chat):
    with pytest.raises(ValueError):
        crud.delete_notification_subscriber_by_data(
            db=session,
            chat=chat,
            notification_type=None
        )
