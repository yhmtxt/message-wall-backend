import os

from dotenv import load_dotenv

load_dotenv()

__PGSQL_USER = os.getenv("PGSQL_USER")
__PGSQL_PASSWORD = os.getenv("PGSQL_PASSWORD")

DATABASE_NAME = "test"
DATABASE_URL = f"postgresql://{__PGSQL_USER}:{__PGSQL_PASSWORD}@127.0.0.1:5432/{DATABASE_NAME}"
