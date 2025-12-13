from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from github_repo_search_api.infrastructure.github_client import (
    GitHubAPIError,
    GitHubClient,
    GitHubRateLimitError,
)
from github_repo_search_api.services.github_search_service import GitHubSearchService
from github_repo_search_api.settings import settings
from github_repo_search_api.web.api.repositories.schema import (
    ErrorResponse,
    RepositoryItem,
    RepositorySearchResponse,
)

router = APIRouter()


def get_github_client() -> GitHubClient:
    """Фабрика для создания экземпляра GitHubClient."""
    return GitHubClient(token=settings.github_token)


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
    summary="Поиск реп на GitHub",
    description=(
        "Поиск реп на GitHub с заданными фильтрами и сохранение "
        "результатов в CSV файл. "
        "CSV файл будет сохранен в директорию static с именем формата: "
        "`repositories_{lang}_{limit}_{offset}.csv`"
    ),
)
async def search_repositories(
    lang: Annotated[
        str,
        Query(
            description="Фильтр по ЯП (например: python, javascript, go)",
            examples=["python", "javascript", "go", "rust"],
        ),
    ],
    service: Annotated[GitHubSearchService, Depends(get_search_service)],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=1000,
            description="Кол-во возвращаемых реп",
        ),
    ] = 10,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Кол-во пропускаемых реп (для пагинации)",
        ),
    ] = 0,
    stars_min: Annotated[
        int,
        Query(
            ge=0,
            description="Минимальное кол-во звезд",
        ),
    ] = 0,
    stars_max: Annotated[
        int | None,
        Query(
            ge=0,
            description="Максимальное кол-во звезд (не ограничено, если не указано)",
        ),
    ] = None,
    forks_min: Annotated[
        int,
        Query(
            ge=0,
            description="Минимальное кол-во форков",
        ),
    ] = 0,
    forks_max: Annotated[
        int | None,
        Query(
            ge=0,
            description="Максимальное кол-во форков (не ограничено, если не указано)",
        ),
    ] = None,
) -> RepositorySearchResponse:
    """
    Поиск реп на GitHub и сохранение в CSV.

    :param lang: ЯП для фильтрации.
    :param service: Экземпляр сервиса поиска (внедряется автоматически).
    :param limit: Количество реп для возврата.
    :param offset: Количество реп для пропуска.
    :param stars_min: Минимальное кол-во звезд.
    :param stars_max: Максимальное кол-во звезд.
    :param forks_min: Минимальное кол-во форков.
    :param forks_max: Максимальное кол-во форков.
    :returns: Ответ с репами и информацией о файле.
    :raises HTTPException: При ошибках GitHub API.
    """
    try:
        filepath, repositories = await service.search_and_save(
            language=lang,
            limit=limit,
            offset=offset,
            stars_min=stars_min,
            stars_max=stars_max,
            forks_min=forks_min,
            forks_max=forks_max,
        )

        response_items = [
            RepositoryItem(
                name=repo.name,
                description=repo.description,
                url=repo.url,
                size=repo.size,
                stars=repo.stars,
                forks=repo.forks,
                issues=repo.issues,
                language=repo.language,
                license=repo.license,
            )
            for repo in repositories
        ]

        return RepositorySearchResponse(
            count=len(response_items),
            filename=filepath.name,
            filepath=str(filepath),
            repositories=response_items,
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
