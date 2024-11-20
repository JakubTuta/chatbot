import typing

import requests
from django.contrib.auth.models import User
from django.db.models.manager import BaseManager
from django.http import QueryDict

from . import models, serializers


def check_required_fields(
    data: dict[str, str] | QueryDict, required_fields: list[str]
) -> list[str]:
    missing_fields = [field for field in required_fields if field not in data]

    return missing_fields


def ask_bot(model: str, message: str, history: list[dict[str, str]]) -> str | None:
    try:
        url = "http://localhost:11434/api/chat"
        request_data = {
            "model": model,
            "messages": history + [{"role": "user", "content": message}],
            "stream": False,
        }
        print(request_data)

        response = requests.post(
            url, json=request_data, headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            response_data = response.json()["message"]["content"]

            return response_data

    except requests.exceptions.RequestException as e:
        return None


def create_message(role: str, message: str) -> models.Message:
    data_dict = {"role": role, "content": message}
    serializer = serializers.MessageSerializer(data=data_dict)
    serializer.is_valid(raise_exception=True)

    model = models.Message.objects.create(**serializer.validated_data)  # type: ignore

    return model


def deserialize_messages(messages: list[models.Message]) -> list[dict[str, str]]:
    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]


def get_chats_for_user(
    user: User, model: models.AIModel, sort: bool = False
) -> BaseManager[models.ChatHistory]:
    chats: BaseManager[models.ChatHistory] = models.ChatHistory.objects.filter(
        user=user
    ).filter(ai_model=model)

    if sort:
        chats = chats.order_by("-last_update_time")

    return chats


def get_chat_history_for_user(
    user: User, model: models.AIModel, chat_id: str
) -> models.ChatHistory | None:
    chats: BaseManager[models.ChatHistory] = get_chats_for_user(user, model)

    return chats.filter(id=chat_id).first()


def add_messages_to_history(
    user: User,
    model: models.AIModel,
    chat_history: models.ChatHistory | None,
    messages: list[models.Message],
) -> None:
    if chat_history:
        chat_history.history.extend(messages)
        chat_history.save()

    else:
        chat_history_data: dict[str, typing.Any] = {
            "user": user,
            "ai_model": model,
            "history": messages,
        }

        chat_history = models.ChatHistory.objects.create(**chat_history_data)
        chat_history.save()