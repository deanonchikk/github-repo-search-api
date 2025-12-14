import enum
from pathlib import Path
from tempfile import gettempdir

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TEMP_DIR = Path(gettempdir())


class LogLevel(enum.StrEnum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Настройки приложения.

    Все параметры могут быть переопределены через переменные окружения
    с префиксом GITHUB_REPO_SEARCH_API_.

    Пример:
        GITHUB_REPO_SEARCH_API_PORT=9000
        GITHUB_REPO_SEARCH_API_GITHUB_TOKEN=ghp_xxxxx
    """

    host: str = "127.0.0.1"
    port: int = 8000

    log_level: LogLevel = LogLevel.INFO

    github_token: str | None = None

    static_dir: Path = Path(__file__).parent / "static"

    @field_validator("github_token")
    @classmethod
    def validate_github_token(cls, v: str | None) -> str | None:
        """
        Валидация GitHub токена.

        Игнорируем плейсхолдеры и пустые значения.
        """
        if not v:
            return None

        placeholders = {
            "your-token-here",
            "your_token_here",
            "token",
            "your_github_token",
        }

        if v.lower() in placeholders:
            return None

        if len(v) < 20:
            return None

        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GITHUB_REPO_SEARCH_API_",
        env_file_encoding="utf-8",
    )


settings = Settings()
