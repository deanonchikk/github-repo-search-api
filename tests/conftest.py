from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from github_repo_search_api.infrastructure.github_client import GitHubRepository
from github_repo_search_api.web.application import get_app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Backend для pytest плагина anyio.

    :return: Имя backend.
    """
    return "asyncio"


@pytest.fixture
def mock_http_client() -> httpx.AsyncClient:
    """
    Фикстура для создания mock HTTP клиента.

    :return: Настроенный httpx.AsyncClient для тестов.
    """
    return httpx.AsyncClient(
        base_url="https://api.github.com",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30.0,
    )


@pytest.fixture
def fastapi_app(mock_http_client: httpx.AsyncClient) -> FastAPI:
    """
    Фикстура для создания FastAPI приложения.

    :param mock_http_client: Mock HTTP клиент для тестов.
    :return: FastAPI приложение с замоканными зависимостями.
    """
    application = get_app()
    # Инициализируем http_client в state для тестов
    application.state.http_client = mock_http_client
    # Пересоздаем middleware stack чтобы он видел обновленный state
    application.middleware_stack = None
    application.middleware_stack = application.build_middleware_stack()
    return application


@pytest.fixture
async def client(
    fastapi_app: FastAPI, anyio_backend: Any
) -> AsyncGenerator[AsyncClient]:
    """
    Фикстура для создания клиента тестирования сервера.

    :param fastapi_app: Приложение.
    :yield: Клиент для приложения.
    """
    async with AsyncClient(
        transport=ASGITransport(fastapi_app), base_url="http://test", timeout=2.0
    ) as ac:
        yield ac


@pytest.fixture
def mock_github_response() -> dict[str, Any]:
    """Создать mock ответ GitHub API."""
    return {
        "total_count": 2,
        "incomplete_results": False,
        "items": [
            {
                "name": "test-repo-1",
                "owner": {"login": "test-owner-1"},
                "stargazers_count": 1000,
                "watchers_count": 1000,
                "forks_count": 500,
                "open_issues_count": 10,
                "language": "Python",
                "html_url": "https://github.com/test-owner-1/test-repo-1",
            },
            {
                "name": "test-repo-2",
                "owner": {"login": "test-owner-2"},
                "stargazers_count": 500,
                "watchers_count": 500,
                "forks_count": 200,
                "open_issues_count": 5,
                "language": "Python",
                "html_url": "https://github.com/test-owner-2/test-repo-2",
            },
        ],
    }


@pytest.fixture
def mock_repositories() -> list[GitHubRepository]:
    """Создать список mock репозиториев."""
    return [
        GitHubRepository(
            name="test-repo-1",
            description="Test repository 1 description",
            url="https://github.com/test-owner-1/test-repo-1",
            size=1024,
            stars=1000,
            forks=500,
            issues=10,
            language="Python",
            license="MIT",
        ),
        GitHubRepository(
            name="test-repo-2",
            description="Test repository 2 description",
            url="https://github.com/test-owner-2/test-repo-2",
            size=2048,
            stars=500,
            forks=200,
            issues=5,
            language="Python",
            license="Apache-2.0",
        ),
    ]
