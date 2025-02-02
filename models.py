from typing import Annotated
from datetime import datetime

from fastapi import Depends
from sqlmodel import SQLModel, Field, create_engine, Session

from configurations import DATABASE_URL


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(nullable=False)
    time: datetime | None = Field(nullable=True)


engine = create_engine(DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
