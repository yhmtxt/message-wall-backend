import time
from typing import Annotated

from pydantic import BaseModel
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlmodel import select, desc, func

from ..models import Message, MessageWithUserName, MessageCreate, User, UserGroup
from ..dependencies import SessionDep, CurrentUserDep, deny_access_if_not_init


class MessagesPage(BaseModel):
    messages: list[MessageWithUserName]
    have_next_page: bool


router = APIRouter(tags=["messages"], dependencies=[Depends(deny_access_if_not_init)])


@router.get("/messages")
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


@router.post("/messages", status_code=201)
def create_new_message(
    session: SessionDep, current_user: CurrentUserDep, message_create: MessageCreate
) -> Message:
    message = Message(
        content=message_create.content, time_stamp=int(time.time()), user=current_user
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


@router.delete("/messages/{message_id}", status_code=204)
def delete_message(session: SessionDep, current_user: CurrentUserDep, message_id: int) -> None:
    message = session.get(Message, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if current_user is not message.user and current_user.user_group is not UserGroup.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    session.delete(message)
    session.commit()
