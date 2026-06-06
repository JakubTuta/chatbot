import logging
import threading

from django.db import close_old_connections
from helpers import decorators
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import functions, models, scrape_ollama, serializers

logger = logging.getLogger(__name__)


class AIModels(APIView):
    # url: /ai-models/

    def get(self, request: Request) -> Response:
        all_models = models.AIModel.objects.prefetch_related("versions").order_by("-popularity")
        deserialized_models = serializers.AIModelSerializer(all_models, many=True).data
        return Response(deserialized_models, status=status.HTTP_200_OK)

    @decorators.required_query_params(["minPullCount"])
    def put(self, request: Request) -> Response:
        from . import progress_state

        min_pull_count = int(request.query_params.get("minPullCount", 200_000))
        logger.info("Starting background model pull from ollama (minPullCount=%d)", min_pull_count)

        models.AIModel.objects.all().delete()
        progress_state.set_scrape(running=True, total=None, completed=0, current=None, error=None)
        progress_state.broadcast(
            "scrape_progress",
            {"type": "scrape_progress", "running": True, "total": None, "completed": 0, "current": None, "error": None},
            key="scrape",
            force=True,
        )

        def _scrape_worker():
            try:
                close_old_connections()

                def _cb(completed: int, total: int, title: str) -> None:
                    progress_state.set_scrape(total=total, completed=completed, current=title)
                    progress_state.broadcast(
                        "scrape_progress",
                        {"type": "scrape_progress", "running": True, "total": total, "completed": completed, "current": title, "error": None},
                        key="scrape",
                    )

                scrape_ollama.scrape_ollama(min_pull_count, progress_cb=_cb)
                logger.info("Background model pull completed")
                progress_state.set_scrape(running=False, error=None)
                progress_state.broadcast(
                    "scrape_progress",
                    {"type": "scrape_progress", "running": False, "total": None, "completed": 0, "current": None, "error": None},
                    key="scrape",
                    force=True,
                )
            except Exception as e:
                logger.error("Background model pull failed: %s", e)
                progress_state.set_scrape(running=False, error=str(e))
                progress_state.broadcast(
                    "scrape_progress",
                    {"type": "scrape_progress", "running": False, "total": None, "completed": 0, "current": None, "error": str(e)},
                    key="scrape",
                    force=True,
                )

        threading.Thread(target=_scrape_worker, daemon=True).start()

        return Response(
            {"status": "Model pull started"},
            status=status.HTTP_202_ACCEPTED,
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
            "index",
        ]
    )
    def post(self, request: Request) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore
        if request_data["can_process_image"] not in ["true", "false"]:
            return Response(
                {
                    "error": "Invalid value for 'can_process_image', must be 'true' or 'false'"
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
                {"error": "Invalid version data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        found_model = models.AIModel.objects.filter(model=request_data["model"]).first()

        if found_model:
            if functions.get_version_by_parameters(
                found_model, version_data["parameters"]
            ):
                return Response(
                    {"error": "Version already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            models.AIModelVersion.objects.create(
                ai_model=found_model,
                **version_serializer.validated_data  # type: ignore
            )

            return Response(
                {
                    "status": "Model updated",
                    "model": found_model.model,
                    "version": version_data,
                },
                status=status.HTTP_200_OK,
            )

        model_data = {
            "name": request_data["name"],
            "model": request_data["model"],
            "description": request_data["description"],
            "popularity": int(request_data["popularity"]),
            "can_process_image": request_data["can_process_image"] == "true",
            "index": int(request_data["index"]),
        }

        new_model = models.AIModel.objects.create(**model_data)
        models.AIModelVersion.objects.create(
            ai_model=new_model,
            **version_serializer.validated_data  # type: ignore
        )

        return Response(
            {
                "status": "New model created",
                "model": new_model.model,
                "version": version_data,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatHistory(APIView):
    # url: /chat-history/{model}

    def get(self, request: Request, model: str, chat_id: str) -> Response:
        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {"error": "AI model not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            chat_history := functions.get_chat_history(ai_model, chat_id)
        ) is None:
            return Response([], status=status.HTTP_200_OK)

        messages = functions.get_messages_for_chat(chat_history)
        deserialized_messages = functions.deserialize_messages(messages)

        return Response(deserialized_messages, status=status.HTTP_200_OK)


class AllChats(APIView):
    # url: /all-chats/{model}

    def get(self, request: Request, model: str) -> Response:
        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {
                    "error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_histories = functions.get_chats(ai_model, sort=True)
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
                    "error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = serializers.ChatHistorySerializer(
            data=request.data, context={"ai_model": ai_model}
        )

        if not serializer.is_valid():
            return Response(
                {
                    "error": "Invalid chat data",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        chat_history = serializer.save()

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
                    "error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_history = functions.get_chat_history(ai_model, request_data["chat_id"])

        if not chat_history:
            return Response(
                {
                    "error": "Chat not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_history.delete()
        return Response(
            {
                "status": "Chat deleted",
            },
            status=status.HTTP_200_OK,
        )

    @decorators.required_body_params(["id", "title"])
    def put(self, request: Request, model: str) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {
                    "error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            chat_history := functions.get_chat_history(ai_model, request_data["id"])
        ) is None:
            return Response(
                {
                    "error": "Chat not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_history.title = request_data["title"]
        chat_history.save()

        return Response(
            {
                "status": "Chat title updated",
            },
            status=status.HTTP_200_OK,
        )


class AskBot(APIView):
    # url: /ask-bot/{model}/{chat_id}?parameters={parameters}

    @decorators.required_query_params(["parameters"])
    @decorators.required_body_params(["message"])
    def post(self, request: Request, model: str, chat_id: str) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore

        if (ai_model := models.AIModel.objects.filter(model=model).first()) is None:
            return Response(
                {
                    "error": "AI model not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_history = functions.get_chat_history(ai_model, chat_id)
        existing_messages = functions.get_messages_for_chat(chat_history) if chat_history else []
        history_messages = functions.deserialize_messages(existing_messages)

        user_question = request_data["message"]
        image = request_data.get("image", "")
        model_parameters = request.query_params["parameters"]

        if not (
            bot_response := functions.ask_bot(
                ai_model,
                model_parameters,
                user_question,
                image,
                history_messages,
            )
        ):
            return Response(
                {
                    "error": "Failed to get response from bot",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            functions.add_messages_to_history(
                ai_model, chat_history, user_question, bot_response, image
            )
        except Exception as e:
            return Response(
                {
                    "error": f"Failed to save message: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "status": "Response generated",
                "content": bot_response,
            },
            status=status.HTTP_200_OK,
        )
