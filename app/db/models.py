from typing import Optional, List
from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.orm.dynamic import AppenderQuery

from .database import Base


class ChatType(Base):
    __tablename__ = "chat_types"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String, nullable=False, unique=True)

    # Один ко многим: ChatType -> Chats
    chats: AppenderQuery = relationship(
        "Chat", back_populates="chat_type_model", cascade="all, delete", lazy="dynamic"
    )


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    chat_type = Column(Integer, ForeignKey(ChatType.id, ondelete="CASCADE"), nullable=False)

    # Связь с моделью типа чата
    chat_type_model: "ChatType" = relationship(
        "ChatType", back_populates="chats", lazy="joined"
    )

    # Один к одному: Chat -> User
    user: Optional["User"] = relationship(
        "User", uselist=False, back_populates="chat", cascade="all, delete", lazy="joined"
    )

    # Один к одному: Chat -> Group
    group: Optional["Group"] = relationship(
        "Group", uselist=False, back_populates="chat", cascade="all, delete", lazy="joined"
    )

    # Один ко многим: Chat -> NotificationSubscribers
    notification_subscribers: List["NotificationSubscriber"] = relationship(
        "NotificationSubscriber", back_populates="chat", cascade="all, delete", lazy="selectin"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    chat_id = Column(Integer, ForeignKey(Chat.id, ondelete="CASCADE"), nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)

    # Связь с моделью чата
    chat: "Chat" = relationship(
        "Chat", back_populates="user", lazy="joined"
    )

    # Один к одному: User -> Administrator
    administrator: Optional["Administrator"] = relationship(
        "Administrator", uselist=False, back_populates="user", cascade="all, delete", lazy="joined"
    )


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, nullable=False)
    chat_id = Column(Integer, ForeignKey(Chat.id, ondelete="CASCADE"), nullable=False, unique=True)
    title = Column(String, nullable=False)

    # Связь с моделью чата
    chat: "Chat" = relationship(
        "Chat", back_populates="group", lazy="joined"
    )


class Administrator(Base):
    __tablename__ = "administrators"

    user_id = Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), primary_key=True, nullable=False)
    granted_by = Column(String, nullable=False)
    granted_at = Column(DateTime, nullable=False)

    # Связь с моделью пользователя
    user: "User" = relationship(
        "User", back_populates="administrator", lazy="joined"
    )


class NotificationType(Base):
    __tablename__ = "notification_types"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Один ко многим: NotificationType -> NotificationSubscribers
    subscribers: AppenderQuery = relationship(
        "NotificationSubscriber", back_populates="notification_type_model", cascade="all, delete", lazy="dynamic"
    )


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

    # Связи с моделями Chat и NotificationType
    chat: "Chat" = relationship(
        "Chat", back_populates="notification_subscribers", lazy="joined"
    )

    notification_type_model: "NotificationType" = relationship(
        "NotificationType", back_populates="subscribers", lazy="joined"
    )
