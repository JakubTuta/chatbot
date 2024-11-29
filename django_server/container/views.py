from django_app.models import AIModel
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .ContainerManager import ContainerManager

# Create your views here.


class Docker(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request) -> Response:
        # url: /docker/

        docker_client = ContainerManager()

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"Status": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"Status": "Docker is running"},
            status=status.HTTP_200_OK,
        )


class Containers(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request) -> Response:
        # url: /docker/containers/

        docker_client = ContainerManager()

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"Status": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        containers = docker_client.get_available_containers()

        return Response(containers, status=status.HTTP_200_OK)


class OllamaImage(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request) -> Response:
        # url: /docker/ollama-image/

        docker_client = ContainerManager()

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"Status": "Error connecting to Docker"},
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
                {"Status": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        docker_client.pull_ollama_image()

        return Response(
            {"Status": "ollama/ollama image pulled"},
            status=status.HTTP_200_OK,
        )


class Container(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, model) -> Response:
        # url: /docker/container/{model}

        docker_client = ContainerManager()

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"Status": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not (container := docker_client.get_container(model)):
            return Response(
                {"Status": "Container not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "Status": "Container found",
                "container": ContainerManager.map_container(container),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, model) -> Response:
        # url: /docker/container/{model}?parameters={parameters}

        docker_client = ContainerManager()

        query_model_params: str | None = request.query_params.get("parameters", None)

        if query_model_params is None:
            return Response(
                {"Status": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"Status": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not (ai_model := AIModel.objects.filter(model=model).first()):
            return Response(
                {"Status": "Model not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not (
            ai_model_version := next(
                (
                    version
                    for version in ai_model.versions
                    if version.parameters == query_model_params
                ),
                None,
            )
        ):
            return Response(
                {"Status": "Invalid model version"}, status=status.HTTP_404_NOT_FOUND
            )

        if container := docker_client.run_container(ai_model, ai_model_version):
            return Response(
                {
                    "Status": "Container is running",
                    "container": ContainerManager.map_container(container),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"Status": "Error running container"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def delete(self, request, model) -> Response:
        # url: /docker/container/{model}?parameters={parameters}&method={method}

        docker_client = ContainerManager()

        query_model_params: str | None = request.query_params.get("parameters", None)
        query_method: str | None = request.query_params.get("method", None)

        if query_model_params is None or query_method is None:
            return Response(
                {"Status": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not docker_client.is_connected() and not docker_client.connect_to_docker():
            return Response(
                {"Status": "Error connecting to Docker"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        container_name = f"{model}_{query_model_params}"

        if query_method == "stop":
            docker_client.stop_container(container_name)

            return Response(
                {"Status": "Container stopped"},
                status=status.HTTP_200_OK,
            )

        elif query_method == "remove":
            docker_client.remove_container(container_name)

            return Response(
                {"Status": "Container removed"},
                status=status.HTTP_200_OK,
            )

        else:
            return Response(
                {"Status": "Invalid method"},
                status=status.HTTP_400_BAD_REQUEST,
            )
