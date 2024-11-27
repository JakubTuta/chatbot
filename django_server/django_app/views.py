import typing

from django.contrib.auth.models import User
from django.db.models.manager import BaseManager
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from . import functions, models, serializers


class AIModels(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    # def get_authentication_classes(
    #     self,
    # ) -> list[type[JWTAuthentication]] | list[typing.Any]:
    #     if self.request.method == "POST":
    #         return [JWTAuthentication]
    #     return []

    # def get_permission_classes(
    #     self,
    # ) -> list[type[IsAuthenticated]] | list[type[AllowAny]]:
    #     if self.request.method == "POST":
    #         return [IsAuthenticated]
    #     return [AllowAny]

    def get(self, request) -> Response:
        # url: /ai-models/

        all_models: BaseManager[models.AIModel] = models.AIModel.objects.all().order_by(
            "-popularity"
        )
        deserialized_models = []

        for model in all_models:
            serializer = serializers.AIModelSerializer(model)

            versions = []
            for version in model.versions:
                version_serializer = serializers.AIModelVersionSerializer(version)
                versions.append(version_serializer.data)

            final_model = serializer.data
            final_model.pop("id")  # type: ignore
            final_model["versions"] = versions  # type: ignore

            deserialized_models.append(final_model)

        return Response(deserialized_models, status=status.HTTP_200_OK)

    def post(self, request) -> Response:
        # url: /ai-models/

        required_fields: list[str] = [
            "name",
            "model",
            "description",
            "popularity",
            "can_process_image",
            "parameters",
            "size",
        ]
        if missing_fields := functions.check_required_fields(
            request.data, required_fields
        ):
            return Response(
                {"Error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.data["can_process_image"] not in ["true", "false"]:
            return Response(
                {
                    "Error": "Invalid value for 'can_process_image', must be 'true' or 'false'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        found_model: models.AIModel | None = models.AIModel.objects.filter(
            model=request.data["model"]
        ).first()

        if found_model:
            new_version_data = {
                "parameters": request.data["parameters"],
                "size": request.data["size"],
            }
            new_version_serializer = serializers.AIModelVersionSerializer(
                data=new_version_data
            )

            if not new_version_serializer.is_valid():
                return Response(
                    {"Error": "Invalid version data"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            version_instance = models.AIModelVersion(**new_version_serializer.validated_data)  # type: ignore

            found_model.versions.append(version_instance)
            found_model.save()

            return Response(
                {
                    "Status": "Model updated",
                    "model": found_model.model,
                    "version": {
                        "parameters": new_version_data["parameters"],
                        "size": new_version_data["size"],
                    },
                },
                status=status.HTTP_200_OK,
            )

        new_version_data = {
            "parameters": request.data["parameters"],
            "size": request.data["size"],
        }
        new_version_serializer = serializers.AIModelVersionSerializer(
            data=new_version_data
        )

        if not new_version_serializer.is_valid():
            return Response(
                {"Error": "Invalid version data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_version_instance = models.AIModelVersion(**new_version_serializer.validated_data)  # type: ignore

        new_model_data = {
            "name": request.data["name"],
            "model": request.data["model"],
            "description": request.data["description"],
            "popularity": request.data["popularity"],
            "versions": [new_version_instance],
            "can_process_image": request.data["can_process_image"] == "true",
        }
        new_model_serializer = serializers.AIModelSerializer(data=new_model_data)

        if not new_model_serializer.is_valid():
            return Response(
                {"Error": "Invalid model data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_model_serializer.save()

        return Response(
            {
                "Status": "New model created",
                "model": new_model_data["model"],
                "version": {
                    "parameters": new_version_data["parameters"],
                    "size": new_version_data["size"],
                },
            },
            status=status.HTTP_201_CREATED,
        )


class ChatHistory(APIView):
    authentication_classes: list[type[JWTAuthentication]] = [JWTAuthentication]
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request, model, chat_id) -> Response:
        # url: /chat-history/{model}

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {"Error": "AI model not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user: User = request.user
        if (
            chat_history := functions.get_chat_history_for_user(user, ai_model, chat_id)
        ) is None:
            return Response([], status=status.HTTP_200_OK)

        deserialized_messages = functions.deserialize_messages(chat_history.history)

        return Response(deserialized_messages, status=status.HTTP_200_OK)

    def post(self, request, chat_id) -> Response:
        # url: /chat-history/

        required_fields: list[str] = ["message", "model"]
        if missing_fields := functions.check_required_fields(
            request.data, required_fields
        ):
            return Response(
                {"Error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model: str = request.data["model"]
        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {"Error": "AI model not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user: User = request.user
        chat_history: models.ChatHistory | None = functions.get_chat_history_for_user(
            user, ai_model, chat_id
        )
        chat_history_messages: list[models.Message] = (
            chat_history.history if chat_history else []
        )
        deserialized_chat_history_messages: list[dict[str, str]] = (
            functions.deserialize_messages(chat_history_messages)
        )

        message: str = request.data["message"]
        if (
            bot_response := functions.ask_bot(
                model, message, deserialized_chat_history_messages
            )
        ) is None:
            return Response(
                {"Error": "Failed to get response from bot"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_message: models.Message = functions.create_message("user", message)
            bot_message: models.Message = functions.create_message(
                "assistant", bot_response
            )
        except Exception as e:
            return Response(
                {"Error": f"Failed to create message: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        functions.add_messages_to_history(
            user, ai_model, chat_history, [user_message, bot_message]
        )

        return Response(
            {
                "Status": "Message added to chat history",
                "message": message,
                "response": bot_response,
            },
            status=status.HTTP_200_OK,
        )


class AllChats(APIView):
    authentication_classes: list[type[JWTAuthentication]] = [JWTAuthentication]
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request, model) -> Response:
        # url: /all-chats/{model}

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {"Error": "AI model not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user: User = request.user
        chat_histories: BaseManager[models.ChatHistory] = functions.get_chats_for_user(
            user, ai_model, sort=True
        )

        serializer = serializers.ChatHistorySerializer(chat_histories, many=True)

        response_data = list(
            map(
                lambda chat_history: {
                    "id": chat_history["id"],
                    "title": chat_history["title"],
                },
                serializer.data,
            )
        )

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, model) -> Response:
        # url: /all-chats/{model}

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {"Error": "AI model not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user: User = request.user

        chat_history_data: dict[str, typing.Any] = {
            "user": user,
            "ai_model": ai_model,
            "history": [],
        }

        try:
            chat_history: models.ChatHistory = models.ChatHistory.objects.create(
                **chat_history_data
            )
            chat_history.save()
        except Exception as e:
            return Response(
                {"Error": f"Failed to create new chat: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "Status": "New chat created",
                "id": chat_history.id,  # type: ignore
                "title": "New chat",
            },
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, model) -> Response:
        # url: /all-chats/{model}

        required_fields: list[str] = ["chat_id"]
        if missing_fields := functions.check_required_fields(
            request.data, required_fields
        ):
            return Response(
                {"Error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {"Error": "AI model not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user: User = request.user
        chat_id = request.data["chat_id"]

        chat_histories: models.ChatHistory | None = functions.get_chat_history_for_user(
            user, ai_model, chat_id
        )

        if chat_histories is None:
            return Response(
                {"Error": "Chat not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_histories.delete()

        return Response(
            {"Status": "Chat deleted"},
            status=status.HTTP_200_OK,
        )

    def put(self, request, model) -> Response:
        # url: /all-chats/{model}

        required_fields: list[str] = ["id", "title"]
        if missing_fields := functions.check_required_fields(
            request.data, required_fields
        ):
            return Response(
                {"Error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {"Error": "AI model not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user: User = request.user
        chat_id = request.data["id"]
        title = request.data["title"]

        chat_histories: models.ChatHistory | None = functions.get_chat_history_for_user(
            user, ai_model, chat_id
        )

        if chat_histories is None:
            return Response(
                {"Error": "Chat not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_histories.title = title
        chat_histories.save()

        return Response(
            {"Status": "Chat title updated"},
            status=status.HTTP_200_OK,
        )


class AskBot(APIView):
    authentication_classes: list[type[JWTAuthentication]] = [JWTAuthentication]
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def post(self, request, model, chat_id) -> Response:
        required_fields: list[str] = ["message"]
        if missing_fields := functions.check_required_fields(
            request.data, required_fields
        ):
            return Response(
                {"Error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {"Error": "AI model not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user: User = request.user
        chat_history: models.ChatHistory | None = functions.get_chat_history_for_user(
            user, ai_model, chat_id
        )
        chat_history_messages: list[models.Message] = (
            chat_history.history if chat_history else []
        )
        deserialized_chat_history_messages: list[dict[str, str]] = (
            functions.deserialize_messages(chat_history_messages)
        )

        user_question: str = request.data["message"]
        if (
            bot_response := functions.ask_bot(
                model, user_question, deserialized_chat_history_messages
            )
        ) is None:
            return Response(
                {"Error": "Failed to get response from bot"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_message: models.Message = functions.create_message(
                "user", user_question
            )
            bot_message: models.Message = functions.create_message(
                "assistant", bot_response
            )
        except Exception as e:
            return Response(
                {"Error": f"Failed to create message: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        functions.add_messages_to_history(
            user, ai_model, chat_history, [user_message, bot_message]
        )

        return Response(
            {
                "Status": "Response generated",
                "content": bot_response,
            },
            status=status.HTTP_200_OK,
        )
