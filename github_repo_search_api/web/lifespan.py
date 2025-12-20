from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from github_repo_search_api.settings import settings


def create_http_client() -> httpx.AsyncClient:
    """
    Создание HTTP клиента для GitHub API.

    :returns: Настроенный httpx.AsyncClient с заголовками и базовым URL.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    return httpx.AsyncClient(
        base_url="https://api.github.com",
        headers=headers,
        timeout=30.0,
    )


@asynccontextmanager
async def lifespan_setup(
    app: FastAPI,
) -> AsyncGenerator[None]:  # pragma: no cover
    """
    Контекстный менеджер жизненного цикла приложения.

    Выполняет действия при запуске и завершении приложения:
    - Создает и сохраняет HTTP клиент в app.state
    - Пересобирает middleware stack
    - Автоматически закрывает клиент при остановке

    :param app: Экземпляр FastAPI приложения.
    :yields: Управление передается приложению.
    """
    async with create_http_client() as client:
        app.state.http_client = client
        app.middleware_stack = None
        app.middleware_stack = app.build_middleware_stack()

        yield
