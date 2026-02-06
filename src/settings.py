import enum
import logging
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class LogLevel(str, enum.Enum):
    """Possible log levels."""
    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class ApplicationSettings(BaseSettings):
    """Application-specific settings."""
    model_config = SettingsConfigDict(extra="ignore")  # Ignore extra environment variables
    
    host: str = "0.0.0.0"
    port: int = int(os.environ.get("PORT", "8090"))
    workers_count: int = 3
    reload: bool = True
    environment: str = os.environ.get("ENVIRONMENT", "Development")
    log_level: str = os.environ.get("LOG_LEVEL", "DEBUG")
    app_title: str = "Text2SQL LangGraph Codebase"
    app_version: str = "1.0"
    logging_environment: str = os.environ.get("LOGGING_ENVIRONMENT", "dev")
    
    def model_post_init(self, __context):
        """Post-initialization to handle non-prefixed environment variables."""
        # Fallback to non-prefixed variables for backward compatibility
        if os.environ.get("PORT"):
            try:
                self.port = int(os.environ.get("PORT", str(self.port)))
            except ValueError:
                pass
        
        if os.environ.get("ENVIRONMENT"):
            self.environment = os.environ.get("ENVIRONMENT", self.environment)
        
        if os.environ.get("LOG_LEVEL"):
            self.log_level = os.environ.get("LOG_LEVEL", self.log_level)
        
        if os.environ.get("LOGGING_ENVIRONMENT"):
            self.logging_environment = os.environ.get("LOGGING_ENVIRONMENT", self.logging_environment)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    model_config = SettingsConfigDict(extra="ignore")  # Ignore extra environment variables
    
    POSTGRES_DB_PORT: str | None = os.environ.get("POSTGRES_DB_PORT")
    POSTGRES_DB_PASSWORD: str | None = os.environ.get("POSTGRES_DB_PASSWORD")
    POSTGRES_DB_USERNAME: str | None = os.environ.get("POSTGRES_DB_USERNAME")
    POSTGRES_DB_HOST: str | None = os.environ.get("POSTGRES_DB_HOST")
    POSTGRES_DB_SCHEMA: str | None = os.environ.get("POSTGRES_DB_SCHEMA")
    POSTGRES_DB_NAME: str | None = os.environ.get("POSTGRES_DB_NAME")


    @property
    def url(self) -> URL:
        """Assemble database URL from settings."""
        return URL.build(
            scheme="postgresql+asyncpg",
            host=self.POSTGRES_DB_HOST or "localhost",
            port=int(self.POSTGRES_DB_PORT) if self.POSTGRES_DB_PORT else 5432,
            user=self.POSTGRES_DB_USERNAME or "postgres",
            password=self.POSTGRES_DB_PASSWORD or "",
            path=f"/{self.POSTGRES_DB_NAME or 'postgres'}",
        )
    
    def model_post_init(self, __context):
        """Post-initialization to handle non-prefixed environment variables."""
        # Fallback to non-prefixed variables for backward compatibility
        if not self.POSTGRES_DB_HOST:
            self.POSTGRES_DB_HOST = os.environ.get("POSTGRES_HOST")
        if not self.POSTGRES_DB_PORT:
            port = os.environ.get("POSTGRES_PORT")
            self.POSTGRES_DB_PORT = str(port) if port else None
        if not self.POSTGRES_DB_NAME:
            self.POSTGRES_DB_NAME = os.environ.get("POSTGRES_DB") or os.environ.get("POSTGRES_DB_NAME")
        if not self.POSTGRES_DB_USERNAME:
            self.POSTGRES_DB_USERNAME = os.environ.get("POSTGRES_USER")
        if not self.POSTGRES_DB_PASSWORD:
            self.POSTGRES_DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")

class OpenAISettings(BaseSettings):
    """OpenAI configuration settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )
    
    api_key: str = os.environ.get("OPENAI_API_KEY")
    model: str = os.environ.get("OPENAI_MODEL", "gpt-4o")
    embedding_model: str = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
    
    def model_post_init(self, __context):
        """Post-initialization to handle non-prefixed environment variables."""
        # Fallback to non-prefixed variables for backward compatibility
        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.model:
            self.model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        if not self.embedding_model:
            self.embedding_model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )
    
    redis_host: str = os.environ.get("REDIS_HOST", "localhost")
    redis_port: str = os.environ.get("REDIS_PORT", "6379")
    redis_password: str | None = os.environ.get("REDIS_PASSWORD")
    redis_db: str = os.environ.get("REDIS_DB", "0")


class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(extra="ignore")  # Ignore extra environment variables
    
    app: ApplicationSettings = ApplicationSettings()
    db: DatabaseSettings = DatabaseSettings()
    openai: OpenAISettings = OpenAISettings()
    redis: RedisSettings = RedisSettings()
    
    @property
    def log_level(self) -> str:
        """Return log level as string for backward compatibility."""
        return self.app.log_level

    @property
    def host(self) -> str:
        return self.app.host
    
    @property
    def port(self) -> int:
        return self.app.port
    
    @property
    def workers_count(self) -> int:
        return self.app.workers_count
    
    @property
    def reload(self) -> bool:
        return self.app.reload
    
    @property
    def environment(self) -> str:
        return self.app.environment


settings = Settings()