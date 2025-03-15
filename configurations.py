import os

from dotenv import load_dotenv

load_dotenv()


def get_env_var(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


DATABASE_URL = get_env_var("DATABASE_URL")

JWT_SECRET_KEY = get_env_var("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_DAYS = 7
