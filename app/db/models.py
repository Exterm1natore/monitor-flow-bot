from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


class ChatType(Base):
    __tablename__ = "chat_types"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String, nullable=False, unique=True)

    # Один ко многим: ChatType -> Chats
    chats = relationship("Chat", back_populates="chat_type_model", cascade="all, delete")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    chat_type = Column(Integer, ForeignKey(ChatType.id, ondelete="CASCADE"), nullable=False)

    # Связь с моделью типа чата
    chat_type_model = relationship("ChatType", back_populates="chats")

    # Один к одному: Chat -> User
    user = relationship("User", uselist=False, back_populates="chat", cascade="all, delete")

    # Один к одному: Chat -> Group
    group = relationship("Group", uselist=False, back_populates="chat", cascade="all, delete")

    # Один ко многим: Chat -> NotificationSubscribers
    notification_subscribers = relationship("NotificationSubscriber", back_populates="chat", cascade="all, delete")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    chat_id = Column(Integer, ForeignKey(Chat.id, ondelete="CASCADE"), nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)

    # Связь с моделью чата
    chat = relationship("Chat", back_populates="user")

    # Один к одному: User -> Administrator
    administrator = relationship("Administrator", uselist=False, back_populates="user", cascade="all, delete")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, nullable=False)
    chat_id = Column(Integer, ForeignKey(Chat.id, ondelete="CASCADE"), nullable=False, unique=True)
    title = Column(String, nullable=False)

    # Связь с моделью чата
    chat = relationship("Chat", back_populates="group")


class Administrator(Base):
    __tablename__ = "administrators"

    user_id = Column(Integer, ForeignKey(User.id, ondelete="CASCADE"), primary_key=True, nullable=False)
    granted_by = Column(String, nullable=False)
    granted_at = Column(DateTime, nullable=False)

    # Связь с моделью пользователя
    user = relationship("User", back_populates="administrator")


class NotificationType(Base):
    __tablename__ = "notification_types"

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Один ко многим: NotificationType -> NotificationSubscribers
    subscribers = relationship("NotificationSubscriber", back_populates="notification_type_model", cascade="all, delete")


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
    chat = relationship("Chat", back_populates="notification_subscribers")
    notification_type_model = relationship("NotificationType", back_populates="subscribers")
