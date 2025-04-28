from uuid import UUID
from typing import Annotated

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from ..models import User, UserPublic, UserCreate
from ..dependencies import SessionDep, CurrentUserDep, deny_access_if_not_init
from ..utils import create_access_token, get_password_hash, verify_password


class Token(BaseModel):
    access_token: str
    token_type: str


router = APIRouter(tags=["users"], dependencies=[Depends(deny_access_if_not_init)])


@router.post("/sign_in")
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


@router.post("/sign_up", status_code=201, response_model=UserPublic)
def sign_up(session: SessionDep, user_create: UserCreate) -> User:
    if session.exec(select(User).where(User.name == user_create.name)).first() is not None:
        raise HTTPException(status_code=409, detail="User name already exists")
    user = User(name=user_create.name, hashed_password=get_password_hash(user_create.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/users", response_model=list[UserPublic])
def get_all_users(session: SessionDep) -> list[User]:
    users = session.exec(select(User)).all()
    return list(users)


@router.get("/users/me", response_model=UserPublic)
def get_current_user(current_user: CurrentUserDep) -> User:
    return current_user


@router.get("/users/{user_id}", response_model=UserPublic)
def get_user(session: SessionDep, user_id: UUID) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
