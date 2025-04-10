import time
from contextlib import asynccontextmanager
from uuid import UUID
from typing import Annotated

from pydantic import BaseModel
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, desc, func

from .models import (
    Message,
    MessageWithUserName,
    MessageCreate,
    User,
    UserPublic,
    UserCreate,
    UserGroup,
)
from .dependencies import create_db_and_tables, SessionDep, UserDep
from .utils import create_access_token, get_password_hash, verify_password


class Token(BaseModel):
    access_token: str
    token_type: str


class MessagesPage(BaseModel):
    messages: list[MessageWithUserName]
    have_next_page: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/sign_in")
def sign_in(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = session.exec(select(User).where(User.name == form_data.username)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": str(user.id), "name": user.name})
    return Token(access_token=access_token, token_type="bearer")


@app.post("/sign_up", status_code=201, response_model=UserPublic)
def sign_up(session: SessionDep, user_create: UserCreate) -> User:
    user = User(name=user_create.name, hashed_password=get_password_hash(user_create.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.get("/users", response_model=list[UserPublic])
def get_all_users(session: SessionDep) -> list[User]:
    users = session.exec(select(User)).all()
    return list(users)


@app.get("/users/me", response_model=UserPublic)
def get_current_user(user: UserDep) -> User:
    return user


@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(session: SessionDep, user_id: UUID) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/messages")
def get_messages(session: SessionDep, page: Annotated[int, Query(ge=1)] = 1) -> MessagesPage:
    page_size = 20
    statement = (
        select(Message, User)
        .join(User)
        .order_by(desc(Message.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = session.exec(statement).all()
    messages = [
        MessageWithUserName(**message.model_dump(), user_name=user.name)
        for message, user in result
    ]
    total = session.exec(select(func.count()).select_from(Message)).one()
    have_next_page = page * page_size < total
    return MessagesPage(messages=messages, have_next_page=have_next_page)


@app.post("/messages", status_code=201)
def create_new_message(
    session: SessionDep, user: UserDep, message_create: MessageCreate
) -> Message:
    message = Message(content=message_create.content, time_stamp=int(time.time()), user=user)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


@app.delete("/messages/{id}", status_code=204)
def delete_message(session: SessionDep, user: UserDep, id: int) -> None:
    message = session.get(Message, id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if user is not message.user and user.user_group is not UserGroup.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    session.delete(message)
    session.commit()
