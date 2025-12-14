from pydantic import BaseModel


class Message(BaseModel):
    """Простая модель сообщения."""

    message: str
