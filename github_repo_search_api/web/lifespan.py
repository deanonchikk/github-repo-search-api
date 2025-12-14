from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan_setup(
    app: FastAPI,
) -> AsyncGenerator[None]:  # pragma: no cover
    """
    Контекстный менеджер жизненного цикла приложения.

    Выполняет действия при запуске и завершении приложения.

    :param app: Экземпляр FastAPI приложения.
    :yields: Управление передается приложению.
    """

    app.middleware_stack = None
    app.middleware_stack = app.build_middleware_stack()

    yield
