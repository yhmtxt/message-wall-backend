import os

from dotenv import load_dotenv

load_dotenv()

__PGSQL_HOST = os.getenv("PGSQL_HOST")
__PGSQL_PORT = os.getenv("PGSQL_PORT")
__PGSQL_USER = os.getenv("PGSQL_USER")
__PGSQL_PASSWORD = os.getenv("PGSQL_PASSWORD")

DATABASE_NAME = "massage_wall"
DATABASE_URL = (
    f"postgresql://{__PGSQL_USER}:{__PGSQL_PASSWORD}@{__PGSQL_HOST}:{__PGSQL_PORT}/{DATABASE_NAME}"
)
