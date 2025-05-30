import pytest
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session as SQLAlchemySession

from app.db.crud.universal import _build_condition
from app.db import crud

# Локальный Base для этого модуля
TestBase = declarative_base()


# Локальная модель User
class User(TestBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Фикстуры --- #

@pytest.fixture(scope="function")
def engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="function")
def session(engine) -> SQLAlchemySession:
    TestBase.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    TestBase.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_users(session):
    users = [
        User(name="Alice", created_at=datetime(2023, 1, 1, 10, 0)),
        User(name="Bob", created_at=datetime(2023, 1, 2, 10, 0)),
        User(name="Charlie", created_at=datetime(2023, 1, 3, 10, 0)),
    ]
    session.add_all(users)
    session.commit()
    return users


# --- _build_condition --- #

def test_build_condition_exact_string():
    cond = _build_condition(User, "name", "Alice")
    assert str(cond) == str(User.name == "Alice")


def test_build_condition_partial_string():
    cond = _build_condition(User, "name", "li", partial_match=True)
    assert str(cond) == str(User.name.like("%li%"))


def test_build_condition_partial_date():
    cond = _build_condition(User, "created_at", "2023-01-01", partial_match=True)

    # SQL-функция date(col)
    sql_text = str(cond).lower()
    assert "date(" in sql_text

    # Значение параметра – 2023-01-01
    compiled = cond.compile(compile_kwargs={"literal_binds": True})
    assert "2023-01-01" in str(compiled)


def test_build_condition_unknown_attr_raises():
    with pytest.raises(AttributeError):
        _build_condition(User, "unknown_field", "val")


# --- get_all_records --- #

def test_get_all_records(session, sample_users):
    records = crud.get_all_records(session, User)
    assert len(records) == 3


# --- get_records_range --- #

def test_get_records_range_full(session, sample_users):
    records = crud.get_records_range(session, User, start=1, end=2)
    assert [u.name for u in records] == ["Alice", "Bob"]


def test_get_records_range_from_start(session, sample_users):
    records = crud.get_records_range(session, User, start=2)
    assert [u.name for u in records] == ["Bob", "Charlie"]


def test_get_records_range_to_end(session, sample_users):
    records = crud.get_records_range(session, User, end=2)
    assert [u.name for u in records] == ["Alice", "Bob"]


def test_get_records_range_invalid_range(session, sample_users):
    records = crud.get_records_range(session, User, start=3, end=2)
    assert records == []


def test_get_records_range_order_by_desc(session, sample_users):
    records = crud.get_records_range(session, User, order_by=User.created_at.desc())
    assert records[0].name == "Charlie"


# --- find_one_record --- #

def test_find_one_record_exact_match(session, sample_users):
    user = crud.find_one_record(session, User, {"name": "Alice"})
    assert user.name == "Alice"


def test_find_one_record_partial_match(session, sample_users):
    user = crud.find_one_record(session, User, {"name": "lic"}, partial_match=True)
    assert user.name == "Alice"


def test_find_one_record_none(session):
    user = crud.find_one_record(session, User, {"name": "Unknown"})
    assert user is None


def test_find_one_record_raises_on_no_conditions(session):
    with pytest.raises(ValueError):
        crud.find_one_record(session, User, {})


# --- find_records --- #

def test_find_records_all(session, sample_users):
    results = crud.find_records(session, User, {})
    assert len(results) == 3


def test_find_records_partial(session, sample_users):
    results = crud.find_records(session, User, {"name": "li"}, partial_match=True)
    assert len(results) == 2  # Alice, Charlie


# --- count_records --- #

def test_count_records(session, sample_users):
    count = crud.count_records(session, User)
    assert count == 3
