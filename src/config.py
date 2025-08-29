from enum import StrEnum
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

load_dotenv(override=True)


class AppEnvironment(StrEnum):
    """
    Enum representing different application environments.

    - LOCAL: Indicates that the application is running on a local machine or environment.
    - DEVELOPMENT: Indicates that the application is running in a development environment.
    - PRODUCTION: Indicates that the application is running in a production environment.
    """

    LOCAL = "Local"
    DEVELOPMENT = "Development"
    PRODUCTION = "Production"


class Settings(BaseSettings):
    """
    A settings class for the project defining all the necessary parameters within the
    app through an object.
    """

    # App variables
    ENV: Optional[AppEnvironment] = Field(None, alias="ENV")
    APP_NAME: Optional[str] = Field(None, alias="APP_NAME")
    APP_VERSION: Optional[str] = Field(None, alias="APP_VERSION")
    APP_HOST: Optional[str] = Field(None, alias="APP_HOST")
    APP_PORT: Optional[int] = Field(None, alias="APP_PORT")
    APP_DEBUG: Optional[bool] = Field(False, alias="APP_DEBUG")
    APP_CONTAINER: Optional[bool] = Field(False, alias="APP_CONTAINER")
    DECRYPT_REQUEST_TIME_CHECK: Optional[bool] = Field(
        False, alias="DECRYPT_REQUEST_TIME_CHECK"
    )

    # JWT Token variables
    JWT_SECRET_KEY: Optional[str] = Field(None, alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: Optional[str] = Field(None, alias="JWT_ALGORITHM")
    COOKIES_DOMAIN: Optional[str] = Field(None, alias="COOKIES_DOMAIN")
    ACCESS_TOKEN_EXP: Optional[int] = Field(3600, alias="ACCESS_TOKEN_EXP")
    REFRESH_TOKEN_EXP: Optional[int] = Field(86400, alias="REFRESH_TOKEN_EXP")

    DATABASE_USER: Optional[str] = Field(None, alias="DATABASE_USER")
    DATABASE_PASSWORD: Optional[str] = Field(None, alias="DATABASE_PASSWORD")
    DATABASE_HOST: Optional[str] = Field(None, alias="DATABASE_HOST")
    DATABASE_PORT: Optional[str] = Field(None, alias="DATABASE_PORT")
    DATABASE_NAME: Optional[str] = Field(None, alias="DATABASE_NAME")
    DATABASE_URL: Optional[str] = Field(None, alias="DATABASE_URL")

    # Microsoft SSO Settings
    MICROSOFT_GRAPH_URL: Optional[str] = Field(None, alias="MICROSOFT_GRAPH_URL")
    MICROSOFT_CLIENT_ID: Optional[str] = Field(None, alias="MICROSOFT_CLIENT_ID")
    MICROSOFT_CLIENT_SECRET: Optional[str] = Field(
        None, alias="MICROSOFT_CLIENT_SECRET"
    )
    MICROSOFT_METADATA_URL: Optional[str] = Field(None, alias="MICROSOFT_METADATA_URL")
    MICROSOFT_SCOPE: Optional[str] = Field(None, alias="MICROSOFT_SCOPE")
    MICROSOFT_TOKEN_URL: Optional[str] = Field(None, alias="MICROSOFT_TOKEN_URL")
    SOCIAL_AUTH_ENDPOINT: Optional[str] = Field(None, alias="SOCIAL_AUTH_ENDPOINT")
    SOCIAL_AUTH_REDIRECT_URL: Optional[str] = Field(
        None, alias="SOCIAL_AUTH_REDIRECT_URL"
    )
    MICROSOFT_BASE_URL: Optional[str] = Field(None, alias="MICROSOFT_BASE_URL")
    MICROSOFT_TENANT_ID: Optional[str] = Field(None, alias="MICROSOFT_TENANT_ID")

    GENERATE_CODE_REDIRECT_URL: Optional[str] = Field(
        None, alias="GENERATE_CODE_REDIRECT_URL"
    )
    CODE_REDIRECT_URL: Optional[str] = Field(None, alias="CODE_REDIRECT_URL")

    CELERY_BROKER_URL: Optional[str] = Field(None, alias="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: Optional[str] = Field(None, alias="CELERY_RESULT_BACKEND")

    ACTIVATE_WORKER_SENTRY: Optional[bool] = Field(
        False, alias="ACTIVATE_WORKER_SENTRY"
    )

    LOGIN_REDIRECT_URL: Optional[str] = Field(None, alias="LOGIN_REDIRECT_URL")
    UI_LOGIN_SCREEN: Optional[str] = Field(None, alias="UI_LOGIN_SCREEN")
    LOGIN_REDIRECT_URL_ERROR: Optional[str] = Field(
        None, alias="LOGIN_REDIRECT_URL_ERROR"
    )

    MASTER_ENUM_FILE_PATH: Optional[str] = Field(None, alias="MASTER_ENUM_FILE_PATH")

    REDIS_URL: Optional[str] = Field(None, alias="REDIS_URL")

    PRIVATE_PUBLIC_KEY_PATH: Optional[str] = Field(
        None, alias="PRIVATE_PUBLIC_KEY_PATH"
    )
    PUBLIC_KEY_PATH: Optional[str] = Field(None, alias="PUBLIC_KEY_PATH")

    ENCRYPTION_KEY: Optional[str] = Field(None, alias="ENCRYPTION_KEY")
    SECRET_KEY: Optional[str] = Field(None, alias="SECRET_KEY")

    AICB_URL: Optional[str] = Field(None, alias="AICB_URL")
    AICB_USERNAME: Optional[str] = Field(None, alias="AICB_USERNAME")
    AICB_PASSWORD: Optional[str] = Field(None, alias="AICB_PASSWORD")
    SENTRY_SDK_DSN: Optional[str] = Field(None, alias="SENTRY_SDK_DSN")

    IS_SINGLE_DEVICE_LOGIN_ENABLED: Optional[bool] = Field(
        False, alias="IS_SINGLE_DEVICE_LOGIN_ENABLED"
    )

    WORKER_POOL: Optional[str] = Field(None, alias="WORKER_POOL")
    SENTRY_SDK_DSN: Optional[str] = Field(None, alias="SENTRY_SDK_DSN")

    model_config = {"env_file": ".env", "extra": "ignore"}

    # Add a root validator for required fields
    @model_validator(mode="after")
    def validate_required(self):
        """
        Validate the required fields for the application.
        """
        required_fields = [
            "ENV",
            "JWT_SECRET_KEY",
            "JWT_ALGORITHM",
            "DATABASE_USER",
            "DATABASE_PASSWORD",
            "DATABASE_HOST",
            "DATABASE_PORT",
            "DATABASE_NAME",
        ]
        missing = [field for field in required_fields if not getattr(self, field)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        return self

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_url(cls, val, values) -> str:
        """
        Create a Database URL from the settings provided in the .env file.
        """
        if isinstance(val, str) and val:
            return val

        database_user = values.data.get("DATABASE_USER")
        database_password = values.data.get("DATABASE_PASSWORD")
        database_host = values.data.get("DATABASE_HOST")
        database_port = values.data.get("DATABASE_PORT")
        if database_port:
            database_port = str(database_port).replace('"', "")
        database_name = values.data.get("DATABASE_NAME")

        if not all(
            [
                database_user,
                database_password,
                database_host,
                database_port,
                database_name,
            ]
        ):
            raise ValueError("Incomplete database connection information")
        print(f"postgresql+asyncpg://"
            f"{database_user}:{database_password}@{database_host}:{database_port}/{database_name}")
        return (
            f"postgresql+asyncpg://"
            f"{database_user}:{database_password}@{database_host}:{database_port}/{database_name}"
        )

    @property
    def is_production(self) -> bool:
        """
        Check if the app is running in production mode.
        """
        return self.ENV == AppEnvironment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """
        Check if the app is running in development mode.
        """
        return self.ENV == AppEnvironment.DEVELOPMENT

    @property
    def is_local(self) -> bool:
        """
        Check if the app is running in local mode.
        """
        return self.ENV == AppEnvironment.LOCAL


settings = Settings()
