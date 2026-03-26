import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

load_dotenv()


class Database:
    """
    Database connection and setup class.
    """

    def __init__(self):
        self.engine = None
        self.create_engine()

    def create_engine(self) -> None:
        database_url = settings.DATABASE_URL

        if database_url is None:
            raise ValueError(
                "DATABASE_URL is not set in the environment variables."
            )

        self.engine = (
            create_engine(
                database_url,
                echo=os.getenv("DATABASE_LOG", "False").lower() == "true",
            )
            if database_url
            else None
        )

    def get_engine(self) -> object:
        return self.engine

    def create_db_and_tables(self) -> None:
        if self.engine:
            SQLModel.metadata.create_all(self.engine)
        else:
            raise ValueError(
                "Engine is not initialized."
            )  # TODO: Custom error handling

    def check_connection(self) -> bool:
        try:
            if self.engine:
                with self.engine.connect():
                    # data = connection.execute(text("SELECT * from auth.perfis")) # Simple query to test connection
                    # for row in data:
                    #     print(row)
                    print("[DATABASE - INFO] Database connection successful.")
                return True
            else:
                print("[DATABASE - ERROR] Engine is not initialized.")
                return False
        except Exception as e:
            print(f"[DATABASE - ERROR] Database connection failed: {e}")
            return False


db = Database()


def get_session():
    if not db.engine:
        raise ValueError("Engine is not initialized.")
    with Session(db.engine) as session:
        yield session
