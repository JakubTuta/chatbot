from django.contrib.auth.models import User
from helpers import decorators
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from . import functions, models, scrape_ollama, serializers


class AIModels(APIView):
    # url: /ai-models/

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self) -> Response:
        all_models = models.AIModel.objects.all().order_by("-popularity")
        deserialized_models = []

        for model in all_models:
            model_data = serializers.AIModelSerializer(model).data
            model_data["versions"] = [
                serializers.AIModelVersionSerializer(version).data
                for version in model.versions
            ]
            deserialized_models.append(model_data)

        return Response(deserialized_models, status=status.HTTP_200_OK)

    @decorators.required_query_params(["minPullCount"])
    def put(self, request: Request) -> Response:
        models.AIModel.objects.all().delete()

        min_pull_count = int(request.query_params.get("minPullCount", 200_000))
        success = scrape_ollama.scrape_ollama(min_pull_count)

        if not success:
            return Response(
                {"Error": "Failed to pull new models from ollama"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"Status": "Pulled new models from ollama"},
            status=status.HTTP_200_OK,
        )

    @decorators.required_body_params(
        [
            "name",
            "model",
            "description",
            "popularity",
            "can_process_image",
            "parameters",
            "size",
        ]
    )
    def post(self, request: Request) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore
        if request_data["can_process_image"] not in ["true", "false"]:
            return Response(
                {
                    "Error": "Invalid value for 'can_process_image', must be 'true' or 'false'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        version_data = {
            "parameters": request_data["parameters"],
            "size": request_data["size"],
        }
        version_serializer = serializers.AIModelVersionSerializer(data=version_data)

        if not version_serializer.is_valid():
            return Response(
                {"Error": "Invalid version data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        found_model = models.AIModel.objects.filter(model=request_data["model"]).first()

        if found_model:
            if functions.get_version_by_parameters(
                found_model, version_data["parameters"]
            ):
                return Response(
                    {"Error": "Version already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            version_instance = models.AIModelVersion(
                **version_serializer.validated_data  # type: ignore
            )
            found_model.versions.append(version_instance)
            found_model.save()

            return Response(
                {
                    "Status": "Model updated",
                    "model": found_model.model,
                    "version": version_data,
                },
                status=status.HTTP_200_OK,
            )

        version_instance = models.AIModelVersion(**version_serializer.validated_data)  # type: ignore
        model_data = {
            "name": request_data["name"],
            "model": request_data["model"],
            "description": request_data["description"],
            "popularity": request_data["popularity"],
            "versions": [version_instance],
            "can_process_image": request_data["can_process_image"] == "true",
        }

        model_serializer = serializers.AIModelSerializer(data=model_data)

        if not model_serializer.is_valid():
            return Response(
                {"Error": "Invalid model data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model_serializer.save()

        return Response(
            {
                "Status": "New model created",
                "model": model_data["model"],
                "version": version_data,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatHistory(APIView):
    # url: /chat-history/{model}

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, model: str, chat_id: str) -> Response:
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


class AllChats(APIView):
    # url: /all-chats/{model}

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, model: str) -> Response:
        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {
                    "Error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_histories = functions.get_chats_for_user(request.user, ai_model, sort=True)
        serializer = serializers.ChatHistorySerializer(chat_histories, many=True)

        response_data = [
            {"id": chat["id"], "title": chat["title"]} for chat in serializer.data
        ]

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )

    def post(self, request: Request, model: str) -> Response:
        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {
                    "Error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = serializers.ChatHistorySerializer(
            data=request.data, ai_model=ai_model
        )

        if not serializer.is_valid():
            return Response(
                {
                    "Error": "Invalid chat data",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.required_body_params(["chat_id"])
    def delete(self, request: Request, model: str) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {
                    "Error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_history = functions.get_chat_history_for_user(
            request.user, ai_model, request_data["chat_id"]
        )

        if not chat_history:
            return Response(
                {
                    "Error": "Chat not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_history.delete()
        return Response(
            {
                "Status": "Chat deleted",
            },
            status=status.HTTP_200_OK,
        )

    @decorators.required_body_params(["id", "title"])
    def put(self, request: Request, model: str) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {
                    "Error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            chat_history := functions.get_chat_history_for_user(
                request.user, ai_model, request_data["id"]
            )
        ) is None:
            return Response(
                {
                    "Error": "Chat not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_history.title = request_data["title"]
        chat_history.save()

        return Response(
            {
                "Status": "Chat title updated",
            },
            status=status.HTTP_200_OK,
        )


class AskBot(APIView):
    # url: /ask-bot/{model}/{chat_id}?parameters={parameters}

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @decorators.required_query_params(["parameters"])
    @decorators.required_body_params(["message"])
    def post(self, request: Request, model: str, chat_id: str) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore

        ai_model = models.AIModel.objects.filter(model=model).first()
        if not ai_model:
            return Response(
                {
                    "Error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        chat_history = functions.get_chat_history_for_user(user, ai_model, chat_id)
        history_messages = functions.deserialize_messages(
            chat_history.history if chat_history else []
        )

        user_question = request_data["message"]
        image = request_data.get("image", "")
        model_parameters = request.query_params["parameters"]

        if not (
            bot_response := functions.ask_bot(
                model,
                model_parameters,
                user_question,
                image,
                history_messages,
            )
        ):
            return Response(
                {
                    "Error": "Failed to get response from bot",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            messages = [
                functions.create_message("user", user_question, image),
                functions.create_message("assistant", bot_response),
            ]
            functions.add_messages_to_history(user, ai_model, chat_history, messages)

        except Exception as e:
            return Response(
                {
                    "Error": f"Failed to create message: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "Status": "Response generated",
                "content": bot_response,
            },
            status=status.HTTP_200_OK,
        )
