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
    Поддерживает аутентификацию через персональный токен.
    """

    BASE_URL = "https://api.github.com"
    SEARCH_REPOS_ENDPOINT = "/search/repositories"
    MAX_PER_PAGE = 100

    def __init__(self, token: str | None = None) -> None:
        """
        Инициализация GitHub клиента.

        :param token: Опциональный персональный токен доступа GitHub для аутентификации.
        """
        self._token = token
        self._client: httpx.AsyncClient | None = None

    def _get_headers(self) -> dict[str, str]:
        """
        Формирование заголовков для HTTP запросов.

        :returns: Словарь с заголовками для запросов к GitHub API.
        """
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _ensure_client(self) -> httpx.AsyncClient:
        """
        Гарантирование инициализации HTTP клиента.

        :returns: Инициализированный httpx.AsyncClient.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=self._get_headers(),
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Закрытие HTTP клиента."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

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
        language: str,
        limit: int,
        offset: int = 0,
        stars_min: int = 0,
        stars_max: int | None = None,
        forks_min: int = 0,
        forks_max: int | None = None,
        sort: str = "stars",
        order: str = "desc",
    ) -> list[GitHubRepository]:
        """
        Поиск репозиториев GitHub с заданными фильтрами.

        Автоматически обрабатывает пагинацию для получения
        запрошенного количества результатов.

        :param language: Фильтр по языку программирования.
        :param limit: Кол-во репозиториев для возврата.
        :param offset: Кол-во репозиториев для пропуска.
        :param stars_min: Минимальное кол-во звезд.
        :param stars_max: Максимальное кол-во звезд (None для неограниченного).
        :param forks_min: Минимальное кол-во форков.
        :param forks_max: Максимальное кол-во форков (None для неограниченного).
        :param sort: Поле для сортировки (stars, forks, help-wanted-issues, updated).
        :param order: Порядок сортировки (asc, desc).
        :returns: Список объектов GitHubRepository.
        :raises GitHubRateLimitError: Если превышен лимит запросов.
        :raises GitHubAPIError: Если GitHub API вернул ошибку.
        """
        client = await self._ensure_client()
        query = self._build_query(
            language=language,
            stars_min=stars_min,
            stars_max=stars_max,
            forks_min=forks_min,
            forks_max=forks_max,
        )

        repositories: list[GitHubRepository] = []
        total_needed = offset + limit
        fetched = 0

        while fetched < total_needed:
            page = (fetched // self.MAX_PER_PAGE) + 1
            per_page = min(self.MAX_PER_PAGE, total_needed - fetched)

            params = {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": per_page,
                "page": page,
            }

            logger.debug(
                f"Searching GitHub repositories: query='{query}', "
                f"page={page}, per_page={per_page}",
            )

            response = await client.get(self.SEARCH_REPOS_ENDPOINT, params=params)

            if response.status_code == 401:
                error_data = response.json()
                error_msg = (
                    "GitHub API authentication failed. "
                    "Either remove GITHUB_REPO_SEARCH_API_GITHUB_TOKEN from .env file "
                    "or provide a valid Personal Access Token from "
                    "https://github.com/settings/tokens"
                )
                raise GitHubAPIError(error_msg)

            if response.status_code == 403:
                error_data = response.json()
                if "rate limit" in error_data.get("message", "").lower():
                    raise GitHubRateLimitError(
                        "GitHub API rate limit exceeded. "
                        "Please try again later or use authentication token.",
                    )
                raise GitHubAPIError(f"GitHub API forbidden: {error_data}")

            if response.status_code != 200:
                raise GitHubAPIError(
                    f"GitHub API error: {response.status_code} - {response.text}",
                )

            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            for _position, item in enumerate(items, start=fetched + 1):
                repo = self._parse_repository(item)
                repositories.append(repo)

            fetched += len(items)

            total_count = data.get("total_count", 0)
            if fetched >= total_count:
                break

        return repositories[offset : offset + limit]

    async def __aenter__(self) -> "GitHubClient":
        """Вход в асинхронный контекстный менеджер."""
        await self._ensure_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Выход из асинхронного контекстного менеджера."""
        await self.close()
