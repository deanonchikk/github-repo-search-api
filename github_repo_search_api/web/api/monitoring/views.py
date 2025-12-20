from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> None:
    """
    Проверка работоспособности приложения.

    Возвращает 200 если приложение работает корректно.
    """
