import csv
from io import StringIO
from pathlib import Path
from typing import ClassVar

from aiofile import async_open
from loguru import logger

from github_repo_search_api.infrastructure.github_client import (
    GitHubClient,
    GitHubRepository,
)
from github_repo_search_api.settings import settings


class GitHubSearchService:
    """Сервис для поиска репозиториев на GitHub и сохранения результатов в CSV файл."""

    CSV_HEADERS: ClassVar[list[str]] = [
        "name",
        "description",
        "url",
        "size",
        "stars",
        "forks",
        "issues",
        "language",
        "license",
    ]

    def __init__(self, client: GitHubClient) -> None:
        """Инициализация сервиса."""
        self._client = client

    def _generate_filename(self, language: str, limit: int, offset: int) -> str:
        """Генерация имени CSV файла."""
        return f"repositories_{language}_{limit}_{offset}.csv"

    def _build_query(
        self,
        *,
        language: str,
        stars_min: int = 0,
        stars_max: int | None = None,
        forks_min: int = 0,
        forks_max: int | None = None,
    ) -> str:
        """
        Формирование строки поискового запроса с использованием GitHub DSL.

        :param language: Фильтр по ЯП.
        :param stars_min: Минимальное кол-во звезд.
        :param stars_max: Максимальное кол-во звезд (None для неограниченного).
        :param forks_min: Минимальное кол-во форков.
        :param forks_max: Максимальное кол-во форков (None для неограниченного).
        :returns: Строка запроса для GitHub search API.
        """
        query_parts = [f"language:{language}"]

        if stars_max is not None:
            query_parts.append(f"stars:{stars_min}..{stars_max}")
        elif stars_min > 0:
            query_parts.append(f"stars:>={stars_min}")

        if forks_max is not None:
            query_parts.append(f"forks:{forks_min}..{forks_max}")
        elif forks_min > 0:
            query_parts.append(f"forks:>={forks_min}")

        return " ".join(query_parts)

    def _repository_to_row(self, repo: GitHubRepository) -> dict[str, str | int]:
        """Преобразование репозитория в строку для CSV."""
        return {
            "name": repo.name,
            "description": repo.description if repo.description else "",
            "url": repo.url,
            "size": repo.size,
            "stars": repo.stars,
            "forks": repo.forks,
            "issues": repo.issues,
            "language": repo.language if repo.language else "",
            "license": repo.license if repo.license else "",
        }

    async def _write_csv(
        self,
        filepath: Path,
        repositories: list[GitHubRepository],
    ) -> None:
        """Запись списка репозиториев в CSV файл асинхронно."""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=self.CSV_HEADERS)
        writer.writeheader()

        for repo in repositories:
            writer.writerow(self._repository_to_row(repo))

        csv_content = output.getvalue()
        output.close()

        filepath.parent.mkdir(parents=True, exist_ok=True)

        async with async_open(filepath, "w", encoding="utf-8") as file:
            await file.write(csv_content)

        logger.info(f"CSV file written: {filepath} ({len(repositories)} repositories)")

    async def search_and_save(
        self,
        *,
        language: str,
        limit: int,
        offset: int = 0,
        stars_min: int = 0,
        stars_max: int | None = None,
        forks_min: int = 0,
        forks_max: int | None = None,
    ) -> tuple[Path, list[GitHubRepository]]:
        """Поиск репозиториев на GitHub и сохранение результатов в CSV файл."""
        logger.info(
            f"Searching GitHub repositories: language={language}, "
            f"limit={limit}, offset={offset}, "
            f"stars={stars_min}..{stars_max}, forks={forks_min}..{forks_max}",
        )

        query = self._build_query(
            language=language,
            stars_min=stars_min,
            stars_max=stars_max,
            forks_min=forks_min,
            forks_max=forks_max,
        )

        repositories = await self._client.search_repositories(
            query=query,
            limit=limit,
            offset=offset,
        )

        filename = self._generate_filename(language, limit, offset)
        filepath = settings.static_dir / filename

        await self._write_csv(filepath, repositories)

        return filepath, repositories
