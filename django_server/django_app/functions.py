import json
import os
import typing

import requests
from container.ContainerManager import ContainerManager
from django.contrib.auth.models import User
from django.db.models.manager import BaseManager
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama

from . import models, serializers


def map_history(history: list[dict[str, str]]) -> list[dict[str, str | list[str]]]:
    return [
        {
            "role": message.get("role", ""),
            "content": message.get("content", ""),
            **(
                {
                    "images": [
                        image.split(",")[1] if len(image.split(",")) > 1 else image
                    ]
                }
                if (image := message.get("image", ""))
                else {}
            ),
        }
        for message in history
    ]


def ask_bot(
    model: models.AIModel,
    parameters: str,
    message: str,
    image: str,
    history: list[dict[str, str]],
) -> str | None:
    container_manager = ContainerManager()

    if (
        container_port := container_manager.get_container_port(model.model, parameters)
    ) is None:
        return None

    is_docker = os.getenv("DOCKER", "false") == "true"
    host_name = "host.docker.internal" if is_docker else "localhost"

    try:
        url = f"http://{host_name}:{container_port}/api/chat/"

        mapped_history = map_history(history)
        new_message = map_history(
            [{"role": "user", "content": message, "image": image}]
        )[0]

        request_data = {
            "model": f"{model.model}:{parameters}",
            "stream": False,
            "messages": mapped_history + [new_message],
        }

        response = requests.post(
            url, json=request_data, headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            response_data = response.json()["message"]["content"]

            return response_data

    except requests.exceptions.RequestException as e:
        print(e)
        return None


def stream_bot_response(
    model: models.AIModel,
    parameters: str,
    message: str,
    image: str,
    history: typing.List[typing.Dict[str, str]],
) -> typing.Generator[str, None, None]:
    """Stream a regular chat response from the model without structured output parsing."""
    container_manager = ContainerManager()

    if (
        container_port := container_manager.get_container_port(model.model, parameters)
    ) is None:
        return

    is_docker = os.getenv("DOCKER", "false") == "true"
    host_name = "host.docker.internal" if is_docker else "localhost"

    try:
        if image:
            new_message = map_history(
                [{"role": "user", "content": message, "image": image}]
            )[0]
        else:
            new_message = map_history([{"role": "user", "content": message}])[0]

        messages = map_history(history) + [new_message]
        base_url = f"http://{host_name}:{container_port}"

        # Regular non-structured chat
        llm = ChatOllama(
            model=f"{model.model}:{parameters}",
            base_url=base_url,
        )

        for chunk in llm.stream(messages):
            yield chunk.text()

    except requests.exceptions.RequestException:
        return


def stream_structured_bot_response(
    model: models.AIModel,
    parameters: str,
    message: str,
    image: str,
    history: typing.List[typing.Dict[str, str]],
    structured_output: typing.List[
        typing.Dict[str, typing.Union[str, typing.Optional[str]]]
    ],
) -> typing.Generator[str, None, None]:
    container_manager = ContainerManager()

    if (
        container_port := container_manager.get_container_port(model.model, parameters)
    ) is None:
        return

    is_docker = os.getenv("DOCKER", "false") == "true"
    host_name = "host.docker.internal" if is_docker else "localhost"

    try:
        if image:
            new_message = map_history(
                [{"role": "user", "content": message, "image": image}]
            )[0]
        else:
            new_message = map_history([{"role": "user", "content": message}])[0]

        messages = map_history(history) + [new_message]
        base_url = f"http://{host_name}:{container_port}"

        properties = {}
        required_fields = []

        for field_spec in structured_output:
            field_name = field_spec["field"]
            field_type = field_spec["type"]
            required_fields.append(field_name)

            if field_type == "string":
                properties[field_name] = {"type": "string"}
            elif field_type == "number":
                properties[field_name] = {"type": "number"}
            elif field_type == "bool":
                properties[field_name] = {"type": "boolean"}
            elif field_type == "date":
                properties[field_name] = {"type": "string", "format": "date"}

            if "description" in field_spec and field_spec["description"]:
                properties[field_name]["description"] = field_spec["description"]

        json_schema = {
            "type": "object",
            "properties": properties,
            "required": required_fields,
        }

        parser = JsonOutputParser(pydantic_object=json_schema)

        system_message = f"""You must respond with JSON that matches the following schema:
```json
{json.dumps(json_schema, indent=2)}
```
Your response should be valid JSON only, with no other text or explanation."""

        system_msg = {"role": "system", "content": system_message}
        messages = [system_msg] + messages

        llm = ChatOllama(
            model=f"{model.model}:{parameters}",
            base_url=base_url,
            format="json",
        )

        response_chunks = []
        for chunk in llm.stream(messages):
            response_chunks.append(chunk.text())

        full_response = "".join(response_chunks)
        try:
            parsed_dict = parser.parse(full_response)
            json_string = json.dumps(parsed_dict, indent=4)
            yield "```json\n"
            yield json_string
            yield "\n```"

        except Exception as e:
            yield f"\n\nError parsing JSON response: {str(e)}"

    except requests.exceptions.RequestException:
        return


def create_message(role: str, message: str, image: str = "") -> models.Message:
    data_dict = {"role": role, "content": message}

    if role == "user" and image:
        data_dict["image"] = image

    serializer = serializers.MessageSerializer(data=data_dict)
    serializer.is_valid(raise_exception=True)

    model = models.Message.objects.create(**serializer.validated_data)  # type: ignore

    return model


def deserialize_messages(messages: list[models.Message]) -> list[dict[str, str]]:
    return [
        {
            "role": message.role,
            "content": message.content,
            "image": message.image,
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


def get_version_by_parameters(
    model: models.AIModel, parameters: str
) -> models.AIModelVersion | None:
    versions = model.versions

    return next(
        (version for version in versions if version.parameters == parameters), None
    )


def get_ai_model(value: str) -> typing.Optional[models.AIModel]:
    try:
        ai_model = models.AIModel.objects.filter(model=value).first()

        return ai_model

    except models.AIModel.DoesNotExist:
        return None
