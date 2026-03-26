import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")  # type: ignore
    SECRET_KEY: str = os.getenv("SECRET_KEY")  # type: ignore
    ALGORITHM: str = os.getenv("ALGORITHM")  # type: ignore
    CRYPT_CONTEXT_SCHEMES: str = os.getenv("CRYPT_CONTEXT_SCHEMES")  # type: ignore
    ACESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACESS_TOKEN_EXPIRE_MINUTES")
    )  # type: ignore
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")
    )  # type: ignore
    ENVIRONMENT = os.getenv("ENVIRONMENT")  # type: ignore

    # MAIL
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME")  # type: ignore
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD")  # type: ignore
    MAIL_FROM: str = os.getenv("MAIL_FROM")  # type: ignore
    MAIL_PORT: int = int(os.getenv("MAIL_PORT"))  # type: ignore
    MAIL_SERVER: str = os.getenv("MAIL_SERVER")  # type: ignore
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS").lower() == "true"  # type: ignore
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS").lower() == "true"  # type: ignore

    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")  # type: ignore


settings = Settings()
