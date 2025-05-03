from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, UniqueConstraint
from .database import Base


class ChatType(Base):
    __tablename__ = "chat_types"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String, nullable=False, unique=True)


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    chat_type = Column(Integer, ForeignKey(ChatType.id, ondelete="CASCADE"), nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    chat_id = Column(Integer, ForeignKey(Chat.id, ondelete="CASCADE"), nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, nullable=False)
    chat_id = Column(Integer, ForeignKey(Chat.id, ondelete="CASCADE"), nullable=False, unique=True)
    title = Column(String, nullable=False)


class Administrator(Base):
    __tablename__ = "administrators"

    user_id = Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), primary_key=True, nullable=False)
    granted_by = Column(String, nullable=False)
    granted_at = Column(DateTime, nullable=False)


class NotificationType(Base):
    __tablename__ = "notification_types"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)


class NotificationSubscriber(Base):
    __tablename__ = "notification_subscribers"

    id = Column(Integer, primary_key=True, nullable=False)
    chat_id = Column(Integer, ForeignKey(Chat.id, ondelete="CASCADE"), nullable=False)
    notification_type = Column(Integer, ForeignKey(NotificationType.id, ondelete="CASCADE"), nullable=False)
    granted_by = Column(String, nullable=False)
    granted_at = Column(DateTime, nullable=False)

    # Добавляет уникальность сочетания двух полей
    __table_args__ = (
        UniqueConstraint(chat_id, notification_type, name='uix_chat_notification_type'),
    )
