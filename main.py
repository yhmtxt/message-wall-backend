from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import User, UserCreate, UserGroup
from .dependencies import create_db_and_tables, SessionDep, InitDep
from .utils import get_password_hash
from .routers import users, messages


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


@app.post("/init", status_code=204, tags=["init"])
def init(session: SessionDep, init: InitDep, user_create: UserCreate) -> None:
    if init:
        raise HTTPException(status_code=400, detail="Application has been initialized")

    admin_user = User(
        name=user_create.name,
        hashed_password=get_password_hash(user_create.password),
        user_group=UserGroup.ADMIN,
    )
    session.add(admin_user)
    session.commit()


app.include_router(users.router)
app.include_router(messages.router)
