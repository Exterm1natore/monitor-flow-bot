import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core import environment

# Создаём указанные директории к базе данных, если они не существуют
_dir_path = os.path.dirname(environment.DB_PATH)
if _dir_path:
    os.makedirs(_dir_path, exist_ok=True)

DATABASE_URL = f"sqlite:///{environment.DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()
