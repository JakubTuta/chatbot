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


def stream_bot_response(
    model: models.AIModel,
    parameters: str,
    message: str,
    image: str,
    history: typing.List[typing.Dict[str, str]],
) -> typing.Generator[str, None, None]:
    url_info = _get_ollama_url(model.model, parameters)
    if url_info is None:
        return None

    base_url, full_model_string = url_info

    try:
        if image:
            new_message = _map_history(
                [{"role": "user", "content": message, "image": image}]
            )[0]
        else:
            new_message = _map_history([{"role": "user", "content": message}])[0]

        messages = _map_history(history) + [new_message]

        llm = ChatOllama(
            model=full_model_string,
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
) -> typing.Optional[str]:
    url_info = _get_ollama_url(model.model, parameters)
    if url_info is None:
        return None

    base_url, full_model_string = url_info

    try:
        messages = _create_base_messages(message, image, history)

        json_schema = _build_json_schema(structured_output)

        parser = JsonOutputParser(pydantic_object=json_schema)

        system_message = f"""You must respond with JSON that matches the following schema:
```json
{json.dumps(json_schema, indent=2)}
```
Your response should be valid JSON only, with no other text or explanation."""

        if image:
            new_message = _map_history(
                [{"role": "user", "content": message, "image": image}]
            )[0]
        else:
            new_message = _map_history([{"role": "user", "content": message}])[0]

        system_msg = {"role": "system", "content": system_message}
        messages = _map_history(history) + [system_msg] + [new_message]

        llm = ChatOllama(
            model=full_model_string,
            base_url=base_url,
            format="json",
        )

        response_chunks = []
        for chunk in llm.stream(messages):
            response_chunks.append(chunk.text())

        full_response = "".join(response_chunks)
        parsed_dict = parser.parse(full_response)
        json_string = json.dumps(parsed_dict, indent=4)

        return f"```json\n{json_string}\n```"

    except Exception as e:
        print(f"Error in structured bot response: {str(e)}")
        return None


def _map_history(history: list[dict[str, str]]) -> list[dict[str, str | list[str]]]:
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


def _build_json_schema(structured_output):
    properties = {}
    required_fields = []

    valid_simple_types = {"string", "number", "bool", "date"}

    type_mapping = {
        "string": {"type": "string"},
        "number": {"type": "number"},
        "bool": {"type": "boolean"},
        "date": {"type": "string", "format": "date"},
    }

    for field_spec in structured_output:
        field_name = field_spec["field"]
        field_type = field_spec["type"]
        required_fields.append(field_name)

        if field_type in valid_simple_types:
            properties[field_name] = type_mapping[field_type].copy()

        elif field_type == "array":
            if "arrayType" not in field_spec or not field_spec["arrayType"]:
                array_type = "string"
            else:
                array_type = field_spec["arrayType"]

            if array_type not in valid_simple_types:
                array_type = "string"

            properties[field_name] = {
                "type": "array",
                "items": type_mapping[array_type].copy(),
            }

        else:
            properties[field_name] = {"type": "string"}

        if "description" in field_spec and field_spec["description"]:
            properties[field_name]["description"] = field_spec["description"]

    return {
        "type": "object",
        "properties": properties,
        "required": required_fields,
    }


def _create_base_messages(message, image, history):
    if image:
        new_message = _map_history(
            [{"role": "user", "content": message, "image": image}]
        )[0]
    else:
        new_message = _map_history([{"role": "user", "content": message}])[0]

    return _map_history(history) + [new_message]


def _get_ollama_url(model_name, parameters):
    container_manager = ContainerManager()
    container_port = container_manager.get_container_port(model_name, parameters)

    if container_port is None:
        return None

    is_docker = os.getenv("DOCKER", "false") == "true"
    host_name = "host.docker.internal" if is_docker else "localhost"
    base_url = f"http://{host_name}:{container_port}"
    full_model_string = f"{model_name}:{parameters}"

    return base_url, full_model_string


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
            "role": str(message.role),
            "content": str(message.content),
            "image": str(message.image) if message.image else "",
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
    user: User, model: typing.Optional[models.AIModel], chat_id: str
) -> models.ChatHistory | None:
    if model is None:
        return

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
