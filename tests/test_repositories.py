from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from github_repo_search_api.infrastructure.github_client import (
    GitHubAPIError,
    GitHubRateLimitError,
    GitHubRepository,
)
from github_repo_search_api.services.github_search_service import GitHubSearchService


class TestRepositoriesAPI:
    """Тесты для API поиска репозиториев."""

    @pytest.mark.anyio
    async def test_search_repositories_missing_lang(
        self,
        client: AsyncClient,
    ) -> None:
        """Тест запроса без обязательного параметра lang."""
        response = await client.get("/api/repositories/search")
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_search_repositories_invalid_limit(
        self,
        client: AsyncClient,
    ) -> None:
        """Тест запроса с невалидным лимитом."""
        response = await client.get(
            "/api/repositories/search",
            params={"lang": "python", "limit": 0},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_search_repositories_invalid_offset(
        self,
        client: AsyncClient,
    ) -> None:
        """Тест запроса с невалидным смещением."""
        response = await client.get(
            "/api/repositories/search",
            params={"lang": "python", "offset": -1},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_search_repositories_success(
        self,
        fastapi_app: FastAPI,
        mock_repositories: list[GitHubRepository],
        tmp_path: Path,
    ) -> None:
        """Тест успешного поиска репозиториев с мокированным сервисом."""
        from github_repo_search_api.web.api.repositories.views import (
            get_search_service,
        )

        mock_service = MagicMock(spec=GitHubSearchService)
        mock_service.search_and_save = AsyncMock(
            return_value=(tmp_path / "repositories_python_2_0.csv", mock_repositories),
        )

        fastapi_app.dependency_overrides[get_search_service] = lambda: mock_service

        try:
            async with AsyncClient(
                transport=ASGITransport(fastapi_app),
                base_url="http://test",
                timeout=30.0,
            ) as client:
                response = await client.get(
                    "/api/repositories/search",
                    params={
                        "lang": "python",
                        "limit": 2,
                        "offset": 0,
                        "stars_min": 100,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["count"] == 2
                assert data["filename"] == "repositories_python_2_0.csv"
                assert "filepath" in data
        finally:
            fastapi_app.dependency_overrides.clear()

    @pytest.mark.anyio
    async def test_search_repositories_with_all_params(
        self,
        fastapi_app: FastAPI,
        mock_repositories: list[GitHubRepository],
        tmp_path: Path,
    ) -> None:
        """Тест запроса со всеми параметрами."""
        from github_repo_search_api.web.api.repositories.views import (
            get_search_service,
        )

        mock_service = MagicMock(spec=GitHubSearchService)
        mock_service.search_and_save = AsyncMock(
            return_value=(
                tmp_path / "repositories_python_10_5.csv",
                mock_repositories,
            ),
        )

        fastapi_app.dependency_overrides[get_search_service] = lambda: mock_service

        try:
            async with AsyncClient(
                transport=ASGITransport(fastapi_app),
                base_url="http://test",
                timeout=30.0,
            ) as client:
                response = await client.get(
                    "/api/repositories/search",
                    params={
                        "lang": "python",
                        "limit": 10,
                        "offset": 5,
                        "stars_min": 100,
                        "stars_max": 1000,
                        "forks_min": 50,
                        "forks_max": 500,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "count" in data
                assert "filename" in data
                assert "filepath" in data
        finally:
            fastapi_app.dependency_overrides.clear()

    @pytest.mark.anyio
    async def test_search_repositories_rate_limit_error(
        self,
        fastapi_app: FastAPI,
        tmp_path: Path,
    ) -> None:
        """Тест обработки ошибки превышения лимита API."""
        from github_repo_search_api.web.api.repositories.views import (
            get_search_service,
        )

        mock_service = MagicMock(spec=GitHubSearchService)
        mock_service.search_and_save = AsyncMock(
            side_effect=GitHubRateLimitError("Rate limit exceeded"),
        )

        fastapi_app.dependency_overrides[get_search_service] = lambda: mock_service

        try:
            async with AsyncClient(
                transport=ASGITransport(fastapi_app),
                base_url="http://test",
                timeout=30.0,
            ) as client:
                response = await client.get(
                    "/api/repositories/search",
                    params={"lang": "python", "limit": 10},
                )

                assert response.status_code == 429
                data = response.json()
                assert "detail" in data
                assert "rate limit" in data["detail"].lower()
        finally:
            fastapi_app.dependency_overrides.clear()

    @pytest.mark.anyio
    async def test_search_repositories_api_error(
        self,
        fastapi_app: FastAPI,
        tmp_path: Path,
    ) -> None:
        """Тест обработки ошибки GitHub API."""
        from github_repo_search_api.web.api.repositories.views import (
            get_search_service,
        )

        mock_service = MagicMock(spec=GitHubSearchService)
        mock_service.search_and_save = AsyncMock(
            side_effect=GitHubAPIError("GitHub API error"),
        )

        fastapi_app.dependency_overrides[get_search_service] = lambda: mock_service

        try:
            async with AsyncClient(
                transport=ASGITransport(fastapi_app),
                base_url="http://test",
                timeout=30.0,
            ) as client:
                response = await client.get(
                    "/api/repositories/search",
                    params={"lang": "python", "limit": 10},
                )

                assert response.status_code == 502
                data = response.json()
                assert "detail" in data
        finally:
            fastapi_app.dependency_overrides.clear()

    @pytest.mark.anyio
    async def test_search_repositories_limit_boundary(
        self,
        client: AsyncClient,
    ) -> None:
        """Тест запроса с лимитом на максимальной границе."""
        response = await client.get(
            "/api/repositories/search",
            params={"lang": "python", "limit": 1000},
        )
        assert response.status_code != 422

    @pytest.mark.anyio
    async def test_search_repositories_limit_over_max(
        self,
        client: AsyncClient,
    ) -> None:
        """Тест запроса с лимитом выше максимума."""
        response = await client.get(
            "/api/repositories/search",
            params={"lang": "python", "limit": 1001},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_search_repositories_stars_validation(
        self,
        client: AsyncClient,
    ) -> None:
        """Тест валидации отрицательных значений звёзд."""
        response = await client.get(
            "/api/repositories/search",
            params={"lang": "python", "stars_min": -1},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_search_repositories_forks_validation(
        self,
        client: AsyncClient,
    ) -> None:
        """Тест валидации отрицательных значений форков."""
        response = await client.get(
            "/api/repositories/search",
            params={"lang": "python", "forks_min": -1},
        )
        assert response.status_code == 422
