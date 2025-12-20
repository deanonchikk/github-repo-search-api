from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, UJSONResponse
from fastapi.staticfiles import StaticFiles

from github_repo_search_api import __version__
from github_repo_search_api.log import configure_logging
from github_repo_search_api.web.api.router import api_router
from github_repo_search_api.web.lifespan import lifespan_setup

APP_ROOT = Path(__file__).parent.parent


def get_app() -> FastAPI:
    """
    Создание и настройка FastAPI приложения.

    Это главная фабрика приложения.

    :return: Настроенное FastAPI приложение.
    """
    configure_logging()
    app = FastAPI(
        title="GitHub Repository Search API",
        description=(
            "API для поиска репозиториев на GitHub и экспорта результатов в CSV файл. "
            "Поддерживает фильтрацию по языку программирования, звездам и форкам."
        ),
        version=__version__,
        lifespan=lifespan_setup,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
        default_response_class=UJSONResponse,
    )

    app.include_router(router=api_router, prefix="/api")
    app.mount("/static", StaticFiles(directory=APP_ROOT / "static"), name="static")

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect to API documentation."""
        return RedirectResponse(url="/api/docs")

    @app.get("/docs", include_in_schema=False)
    async def docs_redirect() -> RedirectResponse:
        """Redirect to API documentation."""
        return RedirectResponse(url="/api/docs")

    @app.get("/redoc", include_in_schema=False)
    async def redoc_redirect() -> RedirectResponse:
        """Redirect to ReDoc documentation."""
        return RedirectResponse(url="/api/redoc")

    return app
