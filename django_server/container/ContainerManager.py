import docker.errors
from docker.models.containers import Container
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

        all_containers = self.__client.containers.list(
            all=True, filters={"ancestor": "ollama/ollama:latest"}
        )

        mapped_containers = []

        for container in all_containers:
            if container.name != "running":
                mapped_containers.append(ContainerManager.map_container(container))
                continue

            docker_exec = container.exec_run("ollama list")
            list_models = docker_exec.output.decode("utf-8").split("\n")

            if len(list_models) < 2 or (
                len(list_models) == 2 and list_models[1].split(" ")[0] == ""
            ):
                mapped_containers.append(
                    ContainerManager.map_container(
                        container,
                        status=ContainerManager.CONTAINER_STATUS["PULLING_MODEL"],
                    )
                )

            else:
                mapped_containers.append(ContainerManager.map_container(container))

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

        container_name = ai_model.name
        network_name = "chatbot_network"
        container_port = 11434 + ai_model.id

        container: Container | None = self.get_container(container_name)

        if container is None:
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
                        "parameters": ai_model_version.parameters,
                        "model": ai_model.model,
                    },
                )

            except docker.errors.DockerException as e:
                print(f"Error creating container: {e}")
                return None

        else:
            container_params = ContainerManager.get_container_environment_variable(
                container, "parameters"
            )

            if container_params:
                container_params += f",{ai_model_version.parameters}"
                ContainerManager.add_container_environment_variable(
                    container, "parameters", container_params
                )
            else:
                ContainerManager.add_container_environment_variable(
                    container, "parameters", ai_model_version.parameters
                )

        container.start()
        container.exec_run(
            f"ollama pull {ai_model.model}:{ai_model_version.parameters}"
        )

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
                ContainerManager.get_container_port(container) if port is None else port
            ),
            "environment": (
                {
                    "parameters": ContainerManager.get_container_environment_variable(
                        container, "parameters"
                    ),
                    "model": ContainerManager.get_container_environment_variable(
                        container, "model"
                    ),
                }
                if environment is None
                else environment
            ),  # type: ignore
        }

    @staticmethod
    def get_container_port(container: Container) -> str | None:
        if container.status != "running":
            return None

        return container.attrs["NetworkSettings"]["Ports"]["11434/tcp"][0]["HostPort"]

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

    @staticmethod
    def add_container_environment_variable(
        container: Container, key: str, value: str
    ) -> None:
        container.attrs["Config"]["Env"].append(f"{key}={value}")
