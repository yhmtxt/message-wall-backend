from contextlib import asynccontextmanager
from typing import Annotated
from datetime import datetime

from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, desc

from models import create_db_and_tables, SessionDep, Message


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


@app.get("/get_messages")
def get_messages(session: SessionDep, page: Annotated[int, Query(ge=1)] = 1):
    statement = select(Message).order_by(desc(Message.id)).offset((page - 1) * 20).limit(20)
    messages = session.exec(statement).all()
    return messages


@app.post("/post_message")
def post_message(session: SessionDep, content: Annotated[str, Body(min_length=1)]):
    message = Message(content=content, time=datetime.today())
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


@app.delete("/delete_message")
def delete_message(session: SessionDep, id: Annotated[int, Body()]):
    message = session.get(Message, id)
    session.delete(message)
    session.commit()
    return {"ok": True}
