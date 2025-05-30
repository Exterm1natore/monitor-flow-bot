import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.db.models import (
    ChatType, Chat, User, Group, Administrator,
    NotificationType, NotificationSubscriber
)


@pytest.fixture
def chat_type(session):
    ct = ChatType(type="private")
    session.add(ct)
    session.commit()
    return ct


@pytest.fixture
def chat(session, chat_type):
    c = Chat(email="test@example.com", chat_type_model=chat_type)
    session.add(c)
    session.commit()
    return c


@pytest.fixture
def user(session, chat):
    u = User(chat=chat, first_name="John", last_name="Doe")
    session.add(u)
    session.commit()
    return u


@pytest.fixture
def group(session, chat):
    g = Group(chat=chat, title="Test Group")
    session.add(g)
    session.commit()
    return g


@pytest.fixture
def notification_type(session):
    nt = NotificationType(type="daily_alert", description="Daily notifications")
    session.add(nt)
    session.commit()
    return nt


def test_user_relationship(chat, user):
    assert user.chat == chat
    assert chat.user == user


def test_group_relationship(chat, group):
    assert group.chat == chat
    assert chat.group == group


def test_create_administrator(session, user):
    admin = Administrator(user=user, granted_by="root", granted_at=datetime.utcnow())
    session.add(admin)
    session.commit()

    assert admin.user == user
    assert user.administrator == admin


def test_delete_user_deletes_admin(session, user):
    admin = Administrator(user=user, granted_by="root", granted_at=datetime.utcnow())
    session.add(admin)
    session.commit()

    session.delete(user)
    session.commit()

    assert session.query(Administrator).count() == 0


def test_create_notification_subscriber(session, chat, notification_type):
    ns = NotificationSubscriber(
        chat=chat,
        notification_type_model=notification_type,
        granted_by="system",
        granted_at=datetime.utcnow()
    )
    session.add(ns)
    session.commit()

    assert ns.chat == chat
    assert ns.notification_type_model == notification_type
    assert chat.notification_subscribers[0] == ns
    assert notification_type.subscribers.first() == ns


def test_unique_notification_subscriber_constraint(session, chat, notification_type):
    ns1 = NotificationSubscriber(
        chat=chat,
        notification_type_model=notification_type,
        granted_by="system",
        granted_at=datetime.utcnow()
    )
    session.add(ns1)
    session.commit()

    ns2 = NotificationSubscriber(
        chat=chat,
        notification_type_model=notification_type,
        granted_by="admin",
        granted_at=datetime.utcnow()
    )
    session.add(ns2)

    with pytest.raises(IntegrityError):
        session.commit()
        session.rollback()


def test_cascade_delete_chat(session, chat, notification_type):
    # Add dependent models
    ns = NotificationSubscriber(
        chat=chat,
        notification_type_model=notification_type,
        granted_by="sys",
        granted_at=datetime.utcnow()
    )
    user = User(chat=chat, first_name="Alice")
    group = Group(chat=chat, title="Group A")
    session.add_all([ns, user, group])
    session.commit()

    session.delete(chat)
    session.commit()

    assert session.query(Chat).count() == 0
    assert session.query(User).count() == 0
    assert session.query(Group).count() == 0
    assert session.query(NotificationSubscriber).count() == 0


def test_chat_type_relationship(chat_type, chat):
    assert chat.chat_type_model == chat_type
    assert chat in chat_type.chats.all()
