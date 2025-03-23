import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from . import functions


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["chat_id"]
        self.room_group_name = f"chat_{self.room_name}"

        self.user = self.scope["user"]
        if self.user.is_anonymous:
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            self.disconnect(1000)

            return

        try:
            text_data_json = json.loads(text_data)

        except json.JSONDecodeError:
            self.disconnect(1000)
            return

        required_keys = ["message", "ai_model", "ai_model_parameters"]
        if not all(key in text_data_json for key in required_keys):
            self.disconnect(1000)
            return

        user_prompt = text_data_json.get("message", "")
        ai_model_value = text_data_json.get("ai_model", "")
        ai_model_parameters = text_data_json.get("ai_model_parameters", "")
        image = text_data_json.get("image", "")

        if (ai_model := functions.get_ai_model(ai_model_value)) is None:
            self.disconnect(1000)
            return

        if (
            chat_history := functions.get_chat_history_for_user(
                self.user, ai_model, self.room_name
            )
        ) is None or chat_history.user != self.user:
            self.disconnect(1000)
            return

        history_messages = functions.deserialize_messages(
            chat_history.history if chat_history else []
        )

        full_response = ""
        for chunks in functions.stream_bot_response(
            ai_model, ai_model_parameters, user_prompt, image, history_messages
        ):
            full_response += chunks
            self.send(text_data=json.dumps({"message": chunks, "done": False}))

        try:
            messages = [
                functions.create_message("user", user_prompt, image),
                functions.create_message("assistant", full_response),
            ]
            functions.add_messages_to_history(
                self.user, ai_model, chat_history, messages
            )

            self.send(text_data=json.dumps({"message": full_response, "done": True}))

        except Exception:
            self.disconnect(1000)

    def chat_message(self, event):
        message = event["message"]

        self.send(text_data=json.dumps({"message": message}))
