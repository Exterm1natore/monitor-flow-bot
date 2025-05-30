import pytest
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.utils.db_records_format import format_for_chat, find_config_model_format, MODEL_FORMATS


# Локальный DeclarativeBase и engine
Base = declarative_base()
engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)


# Локальные модели
class ChatType(Base):
    __tablename__ = "chat_types"
    id = Column(Integer, primary_key=True)
    type = Column(String)


class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    chat_type_id = Column(Integer, ForeignKey("chat_types.id"))
    chat_type_model = relationship("ChatType")


@pytest.fixture(scope="module")
def session():
    Base.metadata.create_all(engine)
    sess = Session()
    yield sess
    sess.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_data(session):
    session.query(Chat).delete()
    session.query(ChatType).delete()
    session.commit()

    ct = ChatType(type="support")
    chat = Chat(email="test@domain.com", chat_type_model=ct)

    session.add_all([ct, chat])
    session.commit()

    return chat


# --- Тесты format_for_chat ---
def test_format_single_flat_fields(sample_data):
    result = format_for_chat(sample_data, model_fields=[Chat.id, Chat.email])
    assert "id=1" in result
    assert "email='test@domain.com'" in result


def test_format_nested_field(sample_data):
    result = format_for_chat(sample_data, model_fields=[
        Chat.id,
        (Chat.chat_type_model, [ChatType.type])
    ])
    assert "chat_type_model={ type='support' }" in result


def test_format_iterable(sample_data):
    result = format_for_chat([sample_data], model_fields=[Chat.id])
    assert result.count("id=") == 1


def test_format_dict():
    data = {"foo": 123, "bar": "baz"}
    result = format_for_chat(data)
    assert result == "{ foo=123, bar='baz' }"


def test_format_primitive():
    assert format_for_chat(42) == "42"
    assert format_for_chat("hello") == "hello"

-b
# --- Тесты find_config_model_format ---
def test_find_config_model_format_found():
    MODEL_FORMATS.append((Chat, [Chat.id, Chat.email], 10))
    config = find_config_model_format("chats")
    assert config is not None
    assert config[0].__tablename__ == "chats"
    MODEL_FORMATS.pop()


def test_find_config_model_format_not_found():
    assert find_config_model_format("non_existing_table") is None