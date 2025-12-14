from pydantic import BaseModel, Field


class RepositoryItem(BaseModel):
    """Информация об одном репозитории."""

    name: str = Field(description="Название репозитория")
    description: str | None = Field(description="Описание репозитория")
    url: str = Field(description="URL репозитория на GitHub")
    size: int = Field(description="Размер репозитория в КБ")
    stars: int = Field(description="Количество звезд")
    forks: int = Field(description="Количество форков")
    issues: int = Field(description="Количество открытых issues")
    language: str | None = Field(description="Основной язык программирования")
    license: str | None = Field(description="Лицензия репозитория")


class RepositorySearchResponse(BaseModel):
    """Ответ на запрос поиска репозиториев."""

    count: int = Field(description="Количество найденных репозиториев")
    filename: str = Field(description="Имя сгенерированного CSV файла")
    filepath: str = Field(description="Путь к сгенерированному CSV файлу")
    repositories: list[RepositoryItem] = Field(
        description="Список найденных репозиториев",
    )


class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой."""

    detail: str = Field(description="Сообщение об ошибке")
