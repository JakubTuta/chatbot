import json
import logging
import os
import time
import typing

import docker
import docker.errors
import requests
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from docker.types.containers import DeviceRequest

logger = logging.getLogger(__name__)


class ContainerManager:
    CONTAINER_STATUS = {
        "RUNNING": "running",
        "EXITED": "exited",
        "PAUSED": "paused",
        "RESTARTING": "restarting",
        "PULLING_MODEL": "pulling_model",
    }

    __client: docker.DockerClient | None = None

    def __init__(self) -> None:
        self.connect_to_docker()

    def is_connected(self) -> bool:
        return self.__client is not None

    def connect_to_docker(self) -> bool:
        try:
            self.__client = docker.DockerClient()

            return True

        except Exception as e:
            logger.warning("Failed to connect to Docker: %s", e)
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

    def ensure_ollama_image(self, progress_cb: typing.Callable | None = None) -> bool:
        if not self.is_connected() or self.__client is None:
            return False

        if self.is_ollama_image_pulled():
            if progress_cb:
                progress_cb(100, "Base image already present")
            return True

        try:
            layer_totals: dict[str, int] = {}
            layer_currents: dict[str, int] = {}
            current_layer_id: str = ""

            for event in self.__client.api.pull(
                "ollama/ollama", tag="latest", stream=True, decode=True
            ):
                layer_id = event.get("id", "")
                progress_detail = event.get("progressDetail") or {}

                if layer_id and progress_detail:
                    total = progress_detail.get("total", 0)
                    current = progress_detail.get("current", 0)
                    if total:
                        layer_totals[layer_id] = total
                        current_layer_id = layer_id
                    if layer_id in layer_totals:
                        layer_currents[layer_id] = current

                if layer_totals and progress_cb:
                    total_bytes = sum(layer_totals.values())
                    current_bytes = sum(layer_currents.get(lid, 0) for lid in layer_totals)
                    overall_pct = int(100 * current_bytes / total_bytes) if total_bytes else 0
                    if current_layer_id and layer_totals.get(current_layer_id):
                        lid_total = layer_totals[current_layer_id]
                        lid_current = layer_currents.get(current_layer_id, 0)
                        layer_pct = int(100 * lid_current / lid_total)
                        detail = f"Layer {current_layer_id[:12]} — {layer_pct}%"
                    else:
                        detail = "Preparing layers…"
                    progress_cb(overall_pct, detail)

            if progress_cb:
                progress_cb(100, "Base image ready")
            return True

        except Exception as e:
            logger.error("Error pulling ollama image: %s", e)
            return False

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
            logger.error("Error retrieving container: %s", e)
            return None

    def run_container(self, ai_model, ai_model_version) -> Container | None:
        """Legacy method kept for compatibility. Prefer create_and_start_container."""
        if not self.is_connected() or self.__client is None:
            return None

        container_name: str = f"{ai_model.model}_{ai_model_version.parameters}"
        network_name = "chatbot-network"
        container_port = 11434 + ai_model.index
        parameters = ai_model_version.parameters

        if (container := self.get_container(container_name)) is not None:
            if container.status == "running":
                return container

            container.start()

            return container

        self.close_any_container_on_port(str(container_port))

        try:
            container = self.__client.containers.create(
                name=container_name,
                image="ollama/ollama:latest",
                detach=True,
                ports={"11434/tcp": container_port},
                network=network_name,
                device_requests=[DeviceRequest(count=-1, capabilities=[["gpu"]])],
                hostname=container_name,
                environment={
                    "model": ai_model.model,
                    "parameters": parameters,
                    "port": container_port,
                },
            )

        except docker.errors.DockerException as e:
            logger.error("Error creating container: %s", e)
            return None

        container.start()
        time.sleep(2)
        try:
            container.exec_run(f"ollama pull {ai_model.model}:{parameters}", detach=True)
        except docker.errors.DockerException as e:
            logger.warning("Failed to exec ollama pull: %s", e)

        return container

    def create_and_start_container(
        self,
        model_name: str,
        parameters: str,
        model_index: int,
    ) -> tuple[Container | None, int | None]:
        if not self.is_connected() or self.__client is None:
            return None, None

        container_name = f"{model_name}_{parameters}"
        network_name = "chatbot-network"
        container_port = 11434 + model_index

        if (container := self.get_container(container_name)) is not None:
            if container.status != "running":
                container.start()
            return container, container_port

        self.close_any_container_on_port(str(container_port))

        try:
            container = self.__client.containers.create(
                name=container_name,
                image="ollama/ollama:latest",
                detach=True,
                ports={"11434/tcp": container_port},
                network=network_name,
                device_requests=[DeviceRequest(count=-1, capabilities=[["gpu"]])],
                hostname=container_name,
                environment={
                    "model": model_name,
                    "parameters": parameters,
                    "port": container_port,
                },
            )
        except docker.errors.DockerException as e:
            logger.error("Error creating container: %s", e)
            return None, None

        container.start()
        return container, container_port

    def wait_for_ollama_ready(self, host_port: int, timeout: int = 60) -> bool:
        is_docker = os.getenv("DOCKER", "false") == "true"
        host = "host.docker.internal" if is_docker else "localhost"
        url = f"http://{host}:{host_port}/api/version"

        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(url, timeout=2)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(1)

        return False

    def pull_model_with_progress(
        self,
        model: str,
        parameters: str,
        host_port: int,
        progress_cb: typing.Callable | None = None,
    ) -> bool:
        is_docker = os.getenv("DOCKER", "false") == "true"
        host = "host.docker.internal" if is_docker else "localhost"
        url = f"http://{host}:{host_port}/api/pull"

        try:
            layer_totals: dict[str, int] = {}
            layer_currents: dict[str, int] = {}
            current_digest: str = ""

            with requests.post(
                url,
                json={"model": f"{model}:{parameters}", "stream": True},
                stream=True,
                timeout=600,
            ) as resp:
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    status = event.get("status", "")
                    digest = event.get("digest", "")
                    total = event.get("total", 0)
                    completed = event.get("completed", 0)

                    if digest:
                        if total:
                            layer_totals[digest] = total
                            current_digest = digest
                        if digest in layer_totals:
                            layer_currents[digest] = completed

                    if layer_totals and progress_cb:
                        total_bytes = sum(layer_totals.values())
                        current_bytes = sum(layer_currents.get(d, 0) for d in layer_totals)
                        overall_pct = int(100 * current_bytes / total_bytes) if total_bytes else 0
                        if current_digest and layer_totals.get(current_digest):
                            d_total = layer_totals[current_digest]
                            d_current = layer_currents.get(current_digest, 0)
                            layer_pct = int(100 * d_current / d_total)
                            short_id = current_digest[7:19] if current_digest.startswith("sha256:") else current_digest[:12]
                            detail = f"Layer {short_id} — {layer_pct}%"
                        else:
                            detail = status or "Pulling…"
                        progress_cb(overall_pct, detail)
                    elif progress_cb and status:
                        progress_cb(0, status)

            if progress_cb:
                progress_cb(100, "Model ready")
            return True

        except Exception as e:
            logger.error("Error pulling model %s:%s: %s", model, parameters, e)
            return False

    def get_network(self, network_name: str) -> Network | None:
        if not self.is_connected() or self.__client is None:
            return None

        try:
            return self.__client.networks.get(network_name)

        except docker.errors.NotFound:
            return None

        except docker.errors.DockerException as e:
            logger.error("Error retrieving network: %s", e)
            return None

    def create_network(self, network_name: str) -> Network | None:
        if not self.is_connected() or self.__client is None:
            return None

        try:
            return self.__client.networks.create(network_name, driver="bridge")

        except docker.errors.DockerException as e:
            logger.error("Error creating network: %s", e)
            return None

    def close_any_container_on_port(self, port: str) -> None:
        if not self.is_connected() or self.__client is None:
            return None

        all_containers: list[Container] = self.__client.containers.list(
            all=True, filters={"ancestor": "ollama/ollama:latest"}
        )

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

    def is_model_pulling(self, model: str, parameters: str) -> bool:
        container_name = f"{model}_{parameters}"
        container = self.get_container(container_name)
        if container is None or container.status != "running":
            return False
        return ContainerManager.is_pulling_model(container)

    def get_container_port(self, model: str, parameters: str) -> str | None:
        if not self.is_connected() or self.__client is None:
            return

        container_name = f"{model}_{parameters}"
        if (
            container := self.get_container(container_name)
        ) is None or container.status != "running":
            return

        container_port = ContainerManager.get_container_environment_variable(
            container, "port"
        )

        return container_port

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
        env_list = container.attrs.get("Config", {}).get("Env") or []

        for env in env_list:
            parts = env.split("=", 1)
            if len(parts) == 2 and parts[0] == env_variable:
                return parts[1]

        return None
