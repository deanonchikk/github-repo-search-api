from fastapi.routing import APIRouter

from github_repo_search_api.web.api import docs, echo, monitoring, repositories

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(docs.router)
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])
api_router.include_router(
    repositories.router,
    prefix="/repositories",
    tags=["repositories"],
)
