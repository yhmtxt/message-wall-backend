import uuid
from enum import StrEnum

from sqlmodel import SQLModel, Field, Relationship


class UserGroup(StrEnum):
    ADMIN = "admin"
    NORMAL = "normal"


class UserBase(SQLModel):
    name: str = Field(nullable=False, unique=True, min_length=1, index=True)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(nullable=False)
    user_group: UserGroup = Field(default=UserGroup.NORMAL)

    messages: list["Message"] = Relationship(back_populates="user", cascade_delete=True)


class UserPublic(UserBase):
    id: uuid.UUID
    user_group: UserGroup
    messages: list["Message"]


class UserCreate(UserBase):
    password: str


class MessageBase(SQLModel):
    content: str = Field(nullable=False, min_length=1, max_length=255)


class Message(MessageBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    time_stamp: int | None = Field(nullable=True)

    user_id: uuid.UUID = Field(
        foreign_key="user.id", default_factory=uuid.uuid4, ondelete="CASCADE"
    )
    user: User = Relationship(back_populates="messages")


class MessageWithUserName(MessageBase):
    id: int
    time_stamp: int | None
    user_name: str
    user_id: uuid.UUID


class MessageCreate(MessageBase): ...
