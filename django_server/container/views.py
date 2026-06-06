import logging
import threading

from django_app.models import AIModel
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .ContainerManager import ContainerManager

logger = logging.getLogger(__name__)


class Docker(APIView):
    def get(self, request) -> Response:
        # url: /docker/

        docker_client = ContainerManager()

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"error": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "Docker is running"},
            status=status.HTTP_200_OK,
        )


class Containers(APIView):
    def get(self, request) -> Response:
        # url: /docker/containers/

        docker_client = ContainerManager()

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"error": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        containers = docker_client.get_available_containers()

        return Response(containers, status=status.HTTP_200_OK)


class OllamaImage(APIView):
    def get(self, request) -> Response:
        # url: /docker/ollama-image/

        docker_client = ContainerManager()

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"error": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if docker_client.is_ollama_image_pulled():
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request) -> Response:
        # url: /docker/ollama-image/

        docker_client = ContainerManager()

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"error": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        threading.Thread(target=docker_client.pull_ollama_image, daemon=True).start()

        return Response(
            {"status": "Pulling ollama/ollama image in background"},
            status=status.HTTP_202_ACCEPTED,
        )


class Container(APIView):
    def get(self, request, model) -> Response:
        # url: /docker/container/{model}

        docker_client = ContainerManager()

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"error": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not (container := docker_client.get_container(model)):
            return Response(
                {"error": "Container not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "status": "Container found",
                "container": ContainerManager.map_container(container),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, model) -> Response:
        # url: /docker/container/{model}?parameters={parameters}
        # Returns 200 synchronously when starting an existing container.
        # Returns 202 and starts a background worker when creating a new container.

        query_model_params = request.query_params.get("parameters", None)
        if query_model_params is None:
            return Response(
                {"error": "Invalid request: missing 'parameters' query param"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        docker_client = ContainerManager()
        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"error": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not (ai_model := AIModel.objects.filter(model=model).first()):
            return Response(
                {"error": "Model not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not (
            ai_model_version := next(
                (
                    version
                    for version in ai_model.versions.all()
                    if version.parameters == query_model_params
                ),
                None,
            )
        ):
            return Response(
                {"error": "Invalid model version"}, status=status.HTTP_404_NOT_FOUND
            )

        container_name = f"{model}_{query_model_params}"

        # If container already exists, start it synchronously (model is already pulled).
        existing = docker_client.get_container(container_name)
        if existing is not None:
            if existing.status != "running":
                existing.start()
            return Response(
                {
                    "status": "Container is running",
                    "container": ContainerManager.map_container(existing),
                },
                status=status.HTTP_200_OK,
            )

        # New container: kick off async worker, return 202 immediately.
        model_name = ai_model.model
        model_index = ai_model.index
        parameters = ai_model_version.parameters

        def _run_worker() -> None:
            from django.db import close_old_connections
            from django_app import progress_state

            close_old_connections()

            def _broadcast_progress(type_: str, percent: int, detail: str) -> None:
                progress_state.set_progress(container_name, phase=type_, percent=percent, detail=detail)
                progress_state.broadcast(
                    type_,
                    {
                        "type": type_,
                        "container": container_name,
                        "phase": type_,
                        "percent": percent,
                        "detail": detail,
                    },
                    key=container_name,
                )

            def _broadcast_final() -> None:
                try:
                    dc = ContainerManager()
                    containers = dc.get_available_containers()
                    snap = progress_state.get_snapshot()
                    progress_state.broadcast(
                        "snapshot",
                        {"type": "snapshot", "containers": containers, **snap},
                        key="final",
                        force=True,
                    )
                except Exception as e:
                    logger.debug("Final broadcast error: %s", e)

            try:
                dc = ContainerManager()
                if not dc.is_connected():
                    dc.connect_to_docker()

                # Step 1: ensure base image with progress
                _broadcast_progress("image_pull_progress", 0, "Checking base image…")

                def image_cb(percent: int, detail: str) -> None:
                    _broadcast_progress("image_pull_progress", percent, detail)

                if not dc.ensure_ollama_image(progress_cb=image_cb):
                    progress_state.clear_progress(container_name)
                    progress_state.broadcast(
                        "container_update",
                        {"type": "container_update", "container": container_name, "error": "Failed to download base image"},
                        key=container_name,
                        force=True,
                    )
                    _broadcast_final()
                    return

                # Step 2: create + start container
                _broadcast_progress("image_pull_progress", 100, "Starting container…")
                container, host_port = dc.create_and_start_container(model_name, parameters, model_index)
                if container is None or host_port is None:
                    progress_state.clear_progress(container_name)
                    progress_state.broadcast(
                        "container_update",
                        {"type": "container_update", "container": container_name, "error": "Failed to create container"},
                        key=container_name,
                        force=True,
                    )
                    _broadcast_final()
                    return

                # Step 3: wait for Ollama to be ready
                _broadcast_progress("model_pull_progress", 0, "Waiting for Ollama to start…")
                if not dc.wait_for_ollama_ready(host_port):
                    logger.warning("Ollama did not become ready on port %s", host_port)

                # Step 4: pull model with progress
                def model_cb(percent: int, detail: str) -> None:
                    _broadcast_progress("model_pull_progress", percent, detail)

                dc.pull_model_with_progress(model_name, parameters, host_port, progress_cb=model_cb)

            except Exception as e:
                logger.error("Container run worker error for %s: %s", container_name, e)
                progress_state.broadcast(
                    "container_update",
                    {"type": "container_update", "container": container_name, "error": str(e)},
                    key=container_name,
                    force=True,
                )
            finally:
                progress_state.clear_progress(container_name)
                _broadcast_final()

        threading.Thread(target=_run_worker, daemon=True, name=f"container-{container_name}").start()

        return Response(
            {"status": "Container creation started"},
            status=status.HTTP_202_ACCEPTED,
        )

    def delete(self, request, model) -> Response:
        # url: /docker/container/{model}?parameters={parameters}&method={method}

        docker_client = ContainerManager()

        query_model_params = request.query_params.get("parameters", None)
        query_method = request.query_params.get("method", None)

        if query_model_params is None or query_method is None:
            return Response(
                {"error": "Invalid request: missing 'parameters' or 'method' query params"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"error": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        container_name = f"{model}_{query_model_params}"

        if query_method == "stop":
            docker_client.stop_container(container_name)

            return Response(
                {"status": "Container stopped"},
                status=status.HTTP_200_OK,
            )

        elif query_method == "remove":
            docker_client.remove_container(container_name)

            return Response(
                {"status": "Container removed"},
                status=status.HTTP_200_OK,
            )

        else:
            return Response(
                {"error": "Invalid method: use 'stop' or 'remove'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
