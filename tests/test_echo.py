import uuid

from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status


async def test_echo(fastapi_app: FastAPI, client: AsyncClient) -> None:
    """
    Проверка работы echo эндпойнта.

    :param fastapi_app: Текущее приложение.
    :param client: Клиент для приложения.
    """
    url = fastapi_app.url_path_for("send_echo_message")
    message = uuid.uuid4().hex
    response = await client.post(url, json={"message": message})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == message
