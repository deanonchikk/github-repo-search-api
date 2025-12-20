import uvicorn

from github_repo_search_api.settings import settings


def main() -> None:
    """Точка входа в приложение."""
    uvicorn.run(
        "github_repo_search_api.web.application:get_app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.value.lower(),
        factory=True,
    )


if __name__ == "__main__":
    main()
