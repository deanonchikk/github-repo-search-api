from pydantic import BaseModel, Field


class RepositorySearchParams(BaseModel):
    """Параметры запроса для поиска реп."""

    limit: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Кол-во возвращаемых реп",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Кол-во пропускаемых реп (для пагинации)",
    )
    lang: str = Field(
        description="Фильтр по ЯП (например: python, javascript, go)",
        examples=["python", "javascript", "go", "rust"],
    )
    stars_min: int = Field(
        default=0,
        ge=0,
        description="Минимальное кол-во звезд",
    )
    stars_max: int | None = Field(
        default=None,
        ge=0,
        description="Максимальное кол-во звезд (не ограничено, если не указано)",
    )
    forks_min: int = Field(
        default=0,
        ge=0,
        description="Минимальное кол-во форков",
    )
    forks_max: int | None = Field(
        default=None,
        ge=0,
        description="Максимальное кол-во форков (не ограничено, если не указано)",
    )


class RepositoryItem(BaseModel):
    """Информация об одной репе."""

    name: str = Field(description="Название репы")
    description: str | None = Field(description="Описание репы")
    url: str = Field(description="URL репы на GitHub")
    size: int = Field(description="Размер репы в КБ")
    stars: int = Field(description="Кол-во звезд")
    forks: int = Field(description="Кол-во форков")
    issues: int = Field(description="Кол-во открытых issues")
    language: str | None = Field(description="Основной ЯП")
    license: str | None = Field(description="Лицензия репы")


class RepositorySearchResponse(BaseModel):
    """Ответ на запрос поиска реп."""

    count: int = Field(description="Кол-во найденных реп")
    filename: str = Field(description="Имя сгенерированного CSV файла")
    filepath: str = Field(description="Путь к сгенерированному CSV файлу")
    repositories: list[RepositoryItem] = Field(
        description="Список найденных реп",
    )


class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой."""

    detail: str = Field(description="Сообщение об ошибке")
