import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import db


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    db.Base.metadata.create_all(bind=engine)
    yield engine
    db.Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()
