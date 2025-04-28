from typing import Annotated, Generator, Callable

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import SQLModel, create_engine, Session, select

from .models import User, UserGroup
from .config import settings

engine = create_engine(settings.DATABASE_URL)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="sign_in")


def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def make_init_checker() -> Callable[[Session], bool]:
    init = False

    def check_if_init(session: SessionDep) -> bool:
        nonlocal init
        if not init:
            admin_user = session.exec(
                select(User).where(User.user_group == UserGroup.ADMIN)
            ).first()
            if admin_user is not None:
                init = True
        return init

    return check_if_init


check_if_init = make_init_checker()

InitDep = Annotated[bool, Depends(check_if_init)]


def deny_access_if_not_init(init: InitDep) -> None:
    if not init:
        raise HTTPException(status_code=400, detail="Application not initialized")
