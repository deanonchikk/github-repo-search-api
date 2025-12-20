from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from loguru import logger

from github_repo_search_api.infrastructure.github_client import (
    GitHubAPIError,
    GitHubClient,
    GitHubRateLimitError,
)
from github_repo_search_api.services.github_search_service import GitHubSearchService
from github_repo_search_api.web.api.repositories.schema import (
    ErrorResponse,
    RepositorySearchParams,
    RepositorySearchResponse,
)

router = APIRouter()


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Получение httpx клиента из state приложения."""
    return request.app.state.http_client


def get_github_client(
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> GitHubClient:
    """Фабрика для создания экземпляра GitHubClient."""
    return GitHubClient(client=http_client)


def get_search_service(
    client: Annotated[GitHubClient, Depends(get_github_client)],
) -> GitHubSearchService:
    """Фабрика для создания экземпляра GitHubSearchService."""
    return GitHubSearchService(client=client)


@router.get(
    "/search",
    response_model=RepositorySearchResponse,
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ErrorResponse,
            "description": "Превышен лимит запросов к GitHub API",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorResponse,
            "description": "Ошибка при обращении к GitHub API",
        },
    },
    summary="Поиск репозиториев на GitHub",
    description=(
        "Поиск репозиториев на GitHub с заданными фильтрами и сохранение "
        "результатов в CSV файл. "
        "CSV файл будет сохранен в директорию static с именем формата: "
        "`repositories_{lang}_{limit}_{offset}.csv`"
    ),
)
async def search_repositories(
    params: Annotated[RepositorySearchParams, Query()],
    service: Annotated[GitHubSearchService, Depends(get_search_service)],
) -> RepositorySearchResponse:
    """
    Поиск репозиториев на GitHub и сохранение в CSV.

    :param params: Параметры поиска репозиториев.
    :param service: Экземпляр сервиса поиска (внедряется автоматически).
    :returns: Ответ с репозиториями и информацией о файле.
    :raises HTTPException: При ошибках GitHub API.
    """
    try:
        filepath, repositories = await service.search_and_save(
            language=params.lang,
            limit=params.limit,
            offset=params.offset,
            stars_min=params.stars_min,
            stars_max=params.stars_max,
            forks_min=params.forks_min,
            forks_max=params.forks_max,
        )

        return RepositorySearchResponse(
            count=len(repositories),
            filename=filepath.name,
            filepath=str(filepath),
        )

    except GitHubRateLimitError as e:
        logger.warning(f"GitHub rate limit exceeded: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        ) from e
    except GitHubAPIError as e:
        logger.error(f"GitHub API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        ) from e
