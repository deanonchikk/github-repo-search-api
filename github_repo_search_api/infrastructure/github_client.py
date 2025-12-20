from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger


@dataclass
class GitHubRepository:
    """Модель данных репозитория GitHub."""

    name: str
    description: str | None
    url: str
    size: int
    stars: int
    forks: int
    issues: int
    language: str | None
    license: str | None


class GitHubClientError(Exception):
    """Базовое исключение для ошибок GitHubClient."""


class GitHubRateLimitError(GitHubClientError):
    """Исключение для ошибок превышения лимита запросов GitHub API."""


class GitHubAPIError(GitHubClientError):
    """Исключение для общих ошибок GitHub API."""


class GitHubClient:
    """
    Асинхронный HTTP клиент для GitHub Search API.

    Использует httpx.AsyncClient для выполнения HTTP запросов к GitHub API.
    Клиент должен быть передан извне и управляться на уровне приложения.
    """

    BASE_URL = "https://api.github.com"
    SEARCH_REPOS_ENDPOINT = "/search/repositories"
    MAX_PER_PAGE = 100

    def __init__(self, client: httpx.AsyncClient) -> None:
        """
        Инициализация GitHub клиента.

        :param client: Инициализированный httpx.AsyncClient для выполнения запросов.
        """
        self._client = client

    def _handle_response_error(self, response: httpx.Response) -> None:
        """
        Обработка ошибок HTTP ответов от GitHub API.

        :param response: Ответ от GitHub API.
        :raises GitHubRateLimitError: При превышении лимита запросов (403 + rate limit).
        :raises GitHubAPIError: При других ошибках API (401, 403, 4**, 5**).
        """
        if response.status_code == 401:
            error_msg = (
                "GitHub API authentication failed. "
                "Either remove GITHUB_REPO_SEARCH_API_GITHUB_TOKEN from .env file "
                "or provide a valid Personal Access Token from "
                "https://github.com/settings/tokens"
            )
            raise GitHubAPIError(error_msg)

        if response.status_code == 403:
            try:
                error_data = response.json()
                if "rate limit" in error_data.get("message", "").lower():
                    raise GitHubRateLimitError(
                        "GitHub API rate limit exceeded. "
                        "Please try again later or use authentication token.",
                    )
            except GitHubRateLimitError:
                raise
            except Exception as e:
                logger.debug(f"Failed to parse GitHub API error response: {e}")

            raise GitHubAPIError(f"GitHub API forbidden: {response.text}")

        if response.status_code >= 400:
            raise GitHubAPIError(
                f"GitHub API error: {response.status_code} - {response.text}",
            )

    def _parse_repository(
        self,
        item: dict[str, Any],
    ) -> GitHubRepository:
        """
        Парсинг элемента ответа GitHub API в GitHubRepository.

        :param item: Сырые данные репы из GitHub API.
        :returns: Объект GitHubRepository.
        """
        license_info = item.get("license")
        license_name = license_info.get("spdx_id") if license_info else None

        return GitHubRepository(
            name=item.get("name", ""),
            description=item.get("description"),
            url=item.get("html_url", ""),
            size=item.get("size", 0),
            stars=item.get("stargazers_count", 0),
            forks=item.get("forks_count", 0),
            issues=item.get("open_issues_count", 0),
            language=item.get("language"),
            license=license_name,
        )

    async def search_repositories(
        self,
        *,
        query: str,
        limit: int,
        offset: int = 0,
        sort: str = "stars",
        order: str = "desc",
    ) -> list[GitHubRepository]:
        """
        Поиск репозиториев GitHub с заданными фильтрами.

        Автоматически обрабатывает пагинацию для получения
        запрошенного количества результатов, начиная с позиции offset.

        :param query: Поисковой запрос в формате GitHub Search DSL.
        :param limit: Кол-во репозиториев для возврата.
        :param offset: Кол-во репозиториев для пропуска с начала результатов.
        :param sort: Поле для сортировки (stars, forks, help-wanted-issues, updated).
        :param order: Порядок сортировки (asc, desc).
        :returns: Список объектов GitHubRepository.
        :raises GitHubRateLimitError: Если превышен лимит запросов.
        :raises GitHubAPIError: Если GitHub API вернул ошибку.
        """
        repositories: list[GitHubRepository] = []

        start_page = (offset // self.MAX_PER_PAGE) + 1
        skip_in_first_page = offset % self.MAX_PER_PAGE

        fetched = 0
        current_page = start_page

        while fetched < limit:
            remaining = limit - fetched
            per_page = min(self.MAX_PER_PAGE, remaining + skip_in_first_page)

            params = {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": per_page,
                "page": current_page,
            }

            logger.debug(
                f"Searching GitHub repositories: query='{query}', "
                f"page={current_page}, per_page={per_page}",
            )

            response = await self._client.get(self.SEARCH_REPOS_ENDPOINT, params=params)

            self._handle_response_error(response)

            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            start_index = skip_in_first_page if current_page == start_page else 0

            for item in items[start_index:]:
                if fetched >= limit:
                    break

                repo = self._parse_repository(item)
                repositories.append(repo)
                fetched += 1

            if len(items) < per_page:
                break

            total_count = data.get("total_count", 0)
            if offset + fetched >= total_count:
                break

            current_page += 1
            skip_in_first_page = 0

        return repositories
