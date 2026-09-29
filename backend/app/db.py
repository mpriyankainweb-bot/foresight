from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from backend.app.config import settings

# connect_args={"check_same_thread": False} is required for SQLite in FastAPI
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
