from pydantic import BaseModel, Field


class RepositorySearchParams(BaseModel):
    """Модель параметров поиска репозиториев."""

    lang: str = Field(
        description="Фильтр по языку программирования",
        examples=["python", "javascript", "go", "rust"],
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Количество возвращаемых репозиториев",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Количество пропускаемых репозиториев",
    )
    stars_min: int = Field(
        default=0,
        ge=0,
        description="Минимальное количество звезд",
    )
    stars_max: int | None = Field(
        default=None,
        ge=0,
        description="Максимальное количество звезд",
    )
    forks_min: int = Field(
        default=0,
        ge=0,
        description="Минимальное количество форков",
    )
    forks_max: int | None = Field(
        default=None,
        ge=0,
        description="Максимальное количество форков",
    )


class RepositorySearchResponse(BaseModel):
    """Ответ на запрос поиска репозиториев."""

    count: int = Field(description="Количество найденных репозиториев")
    filename: str = Field(description="Имя сгенерированного CSV файла")
    filepath: str = Field(description="Путь к сгенерированному CSV файлу")


class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой."""

    detail: str = Field(description="Сообщение об ошибке")
