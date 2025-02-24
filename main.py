import time
from contextlib import asynccontextmanager
from uuid import UUID
from typing import Annotated
from datetime import datetime, timezone, timedelta

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import FastAPI, Body, Query, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, desc, func

from .models import Message, User, UserPublic, UserGroup
from .dependencies import create_db_and_tables, SessionDep, UserDep
from .configurations import JWT_SECRET_KEY, JWT_ALGORITHM, DEFAULT_ACCESS_TOKEN_EXPIRE_DAYS


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict, expire_delta: timedelta | None = None) -> str:
    payload = data.copy()
    if expire_delta is None:
        expire = datetime.now(timezone.utc) + timedelta(days=DEFAULT_ACCESS_TOKEN_EXPIRE_DAYS)
    else:
        expire = datetime.now(timezone.utc) + expire_delta
    payload |= {"exp": expire}
    access_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return access_token


def get_password_hash(password: str) -> str:
    return crypt_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return crypt_context.verify(plain_password, hashed_password)


@app.post("/sign_in")
def sign_in(session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = session.exec(select(User).where(User.name == form_data.username)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": str(user.id), "name": user.name})
    return Token(access_token=access_token, token_type="bearer")


@app.post("/sign_up", status_code=204)
def sign_up(session: SessionDep, name: Annotated[str, Body()], password: Annotated[str, Body()]):
    user = User(name=name, hashed_password=get_password_hash(password))
    session.add(user)
    session.commit()


@app.get("/users/me", response_model=UserPublic)
def get_me(user: UserDep):
    return user


@app.get("/users/{user_id}", response_model=UserPublic)
def get_user(seesion: SessionDep, user_id: UUID):
    user = seesion.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/messages")
def get_messages(session: SessionDep, page: Annotated[int, Query(ge=1)] = 1):
    page_size = 20
    statement = (
        select(Message, User)
        .join(User)
        .order_by(desc(Message.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = session.exec(statement).all()
    messages_with_user_name = [
        {**dict(message), "user_name": user.name} for message, user in result
    ]
    total = session.exec(select(func.count()).select_from(Message)).one()
    have_next_page = page * page_size < total
    return {"messages": messages_with_user_name, "have_next_page": have_next_page}


@app.post("/messages", status_code=204)
def create_new_message(
    session: SessionDep, user: UserDep, content: Annotated[str, Body(min_length=1, max_length=255)]
):
    message = Message(content=content, time_stamp=int(time.time()), user=user)
    session.add(message)
    session.commit()


@app.delete("/messages/{id}", status_code=204)
def delete_message(session: SessionDep, user: UserDep, id: int):
    message = session.get(Message, id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if user is not message.user and user.user_group is not UserGroup.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    session.delete(message)
    session.commit()
