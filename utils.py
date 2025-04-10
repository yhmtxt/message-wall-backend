from datetime import datetime, timezone, timedelta

import jwt
from passlib.context import CryptContext

from .config import settings

crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expire_delta: timedelta | None = None) -> str:
    payload = data.copy()
    if expire_delta is None:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.DEFAULT_ACCESS_TOKEN_EXPIRE_DAYS
        )
    else:
        expire = datetime.now(timezone.utc) + expire_delta
    payload |= {"exp": expire}
    access_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return access_token


def get_password_hash(password: str) -> str:
    return crypt_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return crypt_context.verify(plain_password, hashed_password)
