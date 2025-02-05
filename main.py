from contextlib import asynccontextmanager
from typing import Annotated
from datetime import datetime, timezone

from fastapi import FastAPI, Body, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, desc, func

from .models import create_db_and_tables, SessionDep, Message


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

PAGE_SIZE = 20


@app.get("/get_messages")
def get_messages(session: SessionDep, page: Annotated[int, Query(ge=1)] = 1):
    statement = (
        select(Message).order_by(desc(Message.id)).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    )
    messages = session.exec(statement).all()
    total = session.exec(select(func.count()).select_from(Message)).one()
    have_next_page = page * PAGE_SIZE < total
    return {"messages": messages, "have_next_page": have_next_page}


@app.post("/post_message")
def post_message(session: SessionDep, content: Annotated[str, Body(min_length=1, max_length=255)]):
    message = Message(content=content, time=datetime.now(timezone.utc))
    session.add(message)
    session.commit()
    return {"ok": True}


@app.delete("/delete_message/{id}")
def delete_message(session: SessionDep, id: int):
    message = session.get(Message, id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    session.delete(message)
    session.commit()
    return {"ok": True}
