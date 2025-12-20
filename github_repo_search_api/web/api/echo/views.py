from fastapi import APIRouter

from github_repo_search_api.web.api.echo.schema import Message

router = APIRouter()


@router.post("/")
async def send_echo_message(
    incoming_message: Message,
) -> Message:
    """
    Возвращает эхо-сообщение пользователю.

    :param incoming_message: Входящее сообщение.
    :returns: Сообщение, идентичное входящему.
    """
    return incoming_message
