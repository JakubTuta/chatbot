import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from . import functions

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 10_000
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["chat_id"]
        self.room_group_name = f"chat_{self.room_name}"

        self.user = self.scope["user"]
        if self.user.is_anonymous:
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(  # type: ignore
            self.room_group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(  # type: ignore
            self.room_group_name, self.channel_name
        )

    def _send_error(self, message: str) -> None:
        self.send(text_data=json.dumps({"error": message, "done": True}))

    def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            self.disconnect(1000)
            return

        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON over WebSocket")
            self._send_error("Invalid message format.")
            return

        try:
            required_keys = ["message", "ai_model", "ai_model_parameters"]
            if not all(key in text_data_json for key in required_keys):
                raise ValueError("Missing required keys")

            user_prompt = text_data_json.get("message", "")
            ai_model_value = text_data_json.get("ai_model", "")
            ai_model_parameters = text_data_json.get("ai_model_parameters", "")
            image = text_data_json.get("image", "")
            structured_output = text_data_json.get("structured_output", None)

            if not user_prompt or not isinstance(user_prompt, str):
                raise ValueError("Message must be a non-empty string.")

            if len(user_prompt) > MAX_MESSAGE_LENGTH:
                raise ValueError(
                    f"Message too long. Maximum length is {MAX_MESSAGE_LENGTH} characters."
                )

            if image:
                if not isinstance(image, str) or not image.startswith("data:image/"):
                    raise ValueError("Invalid image format. Expected a base64 data URI.")

                image_data = image.split(",", 1)
                if len(image_data) < 2 or len(image_data[1].encode()) > MAX_IMAGE_SIZE_BYTES:
                    raise ValueError("Image exceeds the maximum allowed size of 5 MB.")

            ai_model = functions.get_ai_model(ai_model_value)
            chat_history = functions.get_chat_history_for_user(
                self.user, ai_model, self.room_name
            )

            if (
                ai_model is None
                or chat_history is None
                or chat_history.user != self.user
            ):
                raise ValueError("Invalid model or chat history.")

            history_messages = functions.deserialize_messages(
                chat_history.history if chat_history else []
            )

            full_response = ""
            if structured_output is None:
                for chunks in functions.stream_bot_response(
                    ai_model, ai_model_parameters, user_prompt, image, history_messages
                ):
                    full_response += chunks
                    self.send(text_data=json.dumps({"message": chunks, "done": False}))

            else:
                full_response = functions.stream_structured_bot_response(
                    ai_model,
                    ai_model_parameters,
                    user_prompt,
                    image,
                    history_messages,
                    structured_output,
                )

                if full_response is None:
                    self.send(
                        text_data=json.dumps(
                            {
                                "message": "Error: Unable to parse the response.",
                                "done": True,
                            }
                        )
                    )
                    return

            messages = [
                functions.create_message("user", user_prompt, image),
                functions.create_message("assistant", full_response),
            ]
            functions.add_messages_to_history(
                self.user, ai_model, chat_history, messages
            )
            self.send(text_data=json.dumps({"message": full_response, "done": True}))

        except ValueError as e:
            logger.warning("Validation error in WebSocket receive: %s", e)
            self._send_error(str(e))
        except Exception:
            logger.exception("Unexpected error in ChatConsumer.receive")
            self._send_error("An unexpected error occurred. Please try again.")

    def chat_message(self, event):
        message = event["message"]

        self.send(text_data=json.dumps({"message": message}))
