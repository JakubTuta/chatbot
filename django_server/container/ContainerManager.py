import time

import docker.errors
from docker.models.containers import Container, ExecResult
from docker.models.images import Image
from docker.models.networks import Network
from docker.types.containers import DeviceRequest

import docker


class ContainerManager:
    CONTAINER_STATUS = {
        "RUNNING": "running",
        "EXITED": "exited",
        "PAUSED": "paused",
        "RESTARTING": "restarting",
        "PULLING_MODEL": "pulling_model",
    }

    def __init__(self) -> None:
        self.connect_to_docker()

    def is_connected(self) -> bool:
        return self.__client is not None

    def connect_to_docker(self) -> bool:
        try:
            self.__client = docker.DockerClient()

            return True

        except Exception as e:
            print(e)
            return False

    def is_ollama_image_pulled(self) -> bool:
        if not self.is_connected() or self.__client is None:
            return False

        try:
            self.__client.images.get("ollama/ollama")

            return True

        except:
            return False

    def pull_ollama_image(self) -> Image | None:
        if not self.is_connected() or self.__client is None:
            return None

        return self.__client.images.pull("ollama/ollama", "latest")

    def get_available_containers(self) -> list[dict[str, str]]:
        if not self.is_connected() or self.__client is None:
            return []

        all_containers: list[Container] = self.__client.containers.list(
            all=True, filters={"ancestor": "ollama/ollama:latest"}
        )

        mapped_containers = []

        for container in all_containers:
            status = container.status
            if status == ContainerManager.CONTAINER_STATUS[
                "RUNNING"
            ] and ContainerManager.is_pulling_model(container):
                status = ContainerManager.CONTAINER_STATUS["PULLING_MODEL"]

            mapped_containers.append(
                ContainerManager.map_container(container, status=status)
            )

        return mapped_containers

    def get_container(self, container_name: str) -> Container | None:
        if not self.is_connected() or self.__client is None:
            return None

        try:
            return self.__client.containers.get(container_name)

        except docker.errors.NotFound:
            return None

        except docker.errors.DockerException as e:
            print(f"Error retrieving container: {e}")
            return None

    def run_container(self, ai_model, ai_model_version) -> Container | None:
        if not self.is_connected() or self.__client is None:
            return None

        container_name = f"{ai_model.model}_{ai_model_version.parameters}"
        network_name = "chatbot_network"
        container_port = 11434 + ai_model.id
        parameters = ai_model_version.parameters

        self.close_any_container_on_port(str(container_port))

        if (container := self.get_container(container_name)) is not None:
            container.start()

            return container

        try:
            if (self.get_network(network_name)) is None and (
                self.create_network(network_name)
            ) is None:
                return None

            container = self.__client.containers.create(
                name=container_name,
                image="ollama/ollama:latest",
                detach=True,
                ports={"11434/tcp": container_port},
                network=network_name,
                network_mode="bridge",
                device_requests=[DeviceRequest(count=-1, capabilities=[["gpu"]])],
                environment={
                    "model": ai_model.model,
                    "parameters": parameters,
                    "port": container_port,
                },
            )

        except docker.errors.DockerException as e:
            print(f"Error creating container: {e}")
            return None

        container.start()
        time.sleep(2)
        container.exec_run(f"ollama pull {ai_model.model}:{parameters}")

        return container

    def get_network(self, network_name: str) -> Network | None:
        if not self.is_connected() or self.__client is None:
            return None

        try:
            return self.__client.networks.get(network_name)

        except docker.errors.NotFound:
            return None

        except docker.errors.DockerException as e:
            print(f"Error retrieving network: {e}")
            return None

    def create_network(self, network_name: str) -> Network | None:
        if not self.is_connected() or self.__client is None:
            return None

        try:
            return self.__client.networks.create(network_name, driver="bridge")

        except docker.errors.DockerException as e:
            print(f"Error creating network: {e}")
            return None

    def close_any_container_on_port(self, port: str) -> None:
        if not self.is_connected() or self.__client is None:
            return None

        all_containers: list[Container] = self.__client.containers.list(
            all=True, filters={"ancestor": "ollama/ollama:latest"}
        )
        print(all_containers)

        for container in all_containers:
            if (
                ContainerManager.get_container_environment_variable(container, "port")
                == port
            ):
                container.stop()

    def stop_container(self, container_name: str) -> None:
        if not self.is_connected() or self.__client is None:
            return

        if (container := self.get_container(container_name)) is not None:
            container.stop()

    def remove_container(self, container_name: str) -> None:
        if not self.is_connected() or self.__client is None:
            return

        if (container := self.get_container(container_name)) is not None:
            container.stop()
            container.remove()

    @staticmethod
    def map_container(
        container: Container,
        name: str | None = None,
        status: str | None = None,
        port: str | None = None,
        environment: dict[str, str | None] | None = None,
    ) -> dict[str, str | None]:
        return {
            "name": container.name or "No name" if name is None else name,
            "status": container.status if status is None else status,
            "port": (
                ContainerManager.get_container_environment_variable(container, "port")
                if port is None
                else port
            ),
            "environment": (
                {
                    "model": ContainerManager.get_container_environment_variable(
                        container, "model"
                    ),
                    "parameters": ContainerManager.get_container_environment_variable(
                        container, "parameters"
                    ),
                }
                if environment is None
                else environment
            ),  # type: ignore
        }

    @staticmethod
    def is_pulling_model(container: Container) -> bool:
        try:
            processes = container.top().get("Processes", [])  # type: ignore

            return any(
                "ollama pull" in process
                for process_list in processes
                for process in process_list
            )

        except (KeyError, IndexError):
            return False

    @staticmethod
    def get_container_environment_variable(
        container: Container, env_variable: str
    ) -> str | None:
        env_list = container.attrs["Config"]["Env"]

        for env in env_list:
            key, value = env.split("=", 1)
            if key == env_variable:
                return value

        return None
