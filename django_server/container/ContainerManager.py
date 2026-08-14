import json
import logging
import os
import threading
import time
import typing

import docker
import docker.errors
import requests
from django.db import transaction
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.networks import Network
from docker.types.containers import DeviceRequest

from .models import ContainerPort

logger = logging.getLogger(__name__)

PORT_RANGE_START = 11434


class ContainerManager:
    CONTAINER_STATUS = {
        "RUNNING": "running",
        "EXITED": "exited",
        "PAUSED": "paused",
        "RESTARTING": "restarting",
        "PULLING_MODEL": "pulling_model",
    }

    # A module-level singleton, not a per-instance client — ContainerManager()
    # is constructed on every chat message, every 2s snapshot tick, and every
    # view, and nothing ever closed the client, leaking a connection each time.
    _client: docker.DockerClient | None = None
    _client_lock = threading.Lock()

    def __init__(self) -> None:
        if ContainerManager._client is None:
            self.connect_to_docker()

    @property
    def client(self) -> docker.DockerClient | None:
        return ContainerManager._client

    def is_connected(self) -> bool:
        if ContainerManager._client is None:
            return False

        try:
            return bool(ContainerManager._client.ping())
        except Exception as e:
            # The client object existing doesn't mean the daemon behind it is
            # still alive — a stale client used to report connected forever
            # after Docker Desktop was quit.
            logger.warning("Docker client failed a health check, dropping it: %s", e)
            ContainerManager._client = None
            return False

    def connect_to_docker(self) -> bool:
        with ContainerManager._client_lock:
            if ContainerManager._client is not None:
                return True

            try:
                ContainerManager._client = docker.DockerClient()

                return True

            except Exception as e:
                logger.warning("Failed to connect to Docker: %s", e)
                return False

    def is_ollama_image_pulled(self) -> bool:
        if not self.is_connected() or self.client is None:
            return False

        try:
            self.client.images.get("ollama/ollama")

            return True

        except docker.errors.DockerException:
            return False

    def pull_ollama_image(self) -> Image | None:
        if not self.is_connected() or self.client is None:
            return None

        return self.client.images.pull("ollama/ollama", "latest")

    def ensure_ollama_image(self, progress_cb: typing.Callable | None = None) -> bool:
        if not self.is_connected() or self.client is None:
            return False

        if self.is_ollama_image_pulled():
            if progress_cb:
                progress_cb(100, "Base image already present")
            return True

        try:
            layer_totals: dict[str, int] = {}
            layer_currents: dict[str, int] = {}
            current_layer_id: str = ""

            for event in self.client.api.pull(
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
        if not self.is_connected() or self.client is None:
            return []

        all_containers: list[Container] = self.client.containers.list(
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
        if not self.is_connected() or self.client is None:
            return None

        try:
            return self.client.containers.get(container_name)

        except docker.errors.NotFound:
            return None

        except docker.errors.DockerException as e:
            logger.error("Error retrieving container: %s", e)
            return None

    @staticmethod
    def allocate_port(container_name: str) -> int:
        """Return the host port owned by `container_name`, allocating the
        lowest free port >= PORT_RANGE_START if it doesn't have one yet.
        Locked so two concurrent container creations can't both compute the
        same free port and collide.
        """
        with transaction.atomic():
            existing = (
                ContainerPort.objects.select_for_update()
                .filter(container_name=container_name)
                .first()
            )
            if existing is not None:
                return existing.port

            used_ports = set(
                ContainerPort.objects.select_for_update().values_list("port", flat=True)
            )
            port = PORT_RANGE_START
            while port in used_ports:
                port += 1

            ContainerPort.objects.create(container_name=container_name, port=port)
            return port

    def create_and_start_container(
        self,
        model_name: str,
        parameters: str,
    ) -> tuple[Container | None, int | None]:
        if not self.is_connected() or self.client is None:
            return None, None

        container_name = f"{model_name}_{parameters}"
        network_name = "chatbot-network"

        if (container := self.get_container(container_name)) is not None:
            if container.status != "running":
                container.start()
                container.reload()
            container_port = ContainerManager.get_container_environment_variable(container, "port")
            return container, int(container_port) if container_port else None

        container_port = ContainerManager.allocate_port(container_name)

        try:
            container = self.client.containers.create(
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
        container.reload()
        return container, container_port

    def wait_for_ollama_ready(self, base_url: str, timeout: int = 60) -> bool:
        url = f"{base_url}/api/version"

        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(url, timeout=2)
                if r.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        return False

    def pull_model_with_progress(
        self,
        model: str,
        parameters: str,
        base_url: str,
        progress_cb: typing.Callable | None = None,
    ) -> tuple[bool, str | None]:
        """Returns (success, error_message). Ollama's /api/pull streams
        `{"error": "..."}` on failure (bad tag, manifest not found, disk
        full) with a 200 status — the request never raises on its own, so
        every line has to be checked for an "error" key or a failed pull
        silently reports 100% / "Model ready" like a success.
        """
        url = f"{base_url}/api/pull"

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
                resp.raise_for_status()

                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if error := event.get("error"):
                        logger.error("Ollama reported a pull error for %s:%s: %s", model, parameters, error)
                        return False, error

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
            return True, None

        except requests.exceptions.RequestException as e:
            logger.error("Error pulling model %s:%s: %s", model, parameters, e)
            return False, str(e)

    def get_network(self, network_name: str) -> Network | None:
        if not self.is_connected() or self.client is None:
            return None

        try:
            return self.client.networks.get(network_name)

        except docker.errors.NotFound:
            return None

        except docker.errors.DockerException as e:
            logger.error("Error retrieving network: %s", e)
            return None

    def create_network(self, network_name: str) -> Network | None:
        if not self.is_connected() or self.client is None:
            return None

        try:
            return self.client.networks.create(network_name, driver="bridge")

        except docker.errors.DockerException as e:
            logger.error("Error creating network: %s", e)
            return None

    def stop_container(self, container_name: str) -> None:
        if not self.is_connected() or self.client is None:
            return

        if (container := self.get_container(container_name)) is not None:
            try:
                container.stop()
            except docker.errors.APIError as e:
                logger.warning("Error stopping container %s: %s", container_name, e)

    def remove_container(self, container_name: str) -> None:
        if not self.is_connected() or self.client is None:
            return

        if (container := self.get_container(container_name)) is not None:
            try:
                container.stop()
                container.remove()
            except docker.errors.APIError as e:
                logger.warning("Error removing container %s: %s", container_name, e)

    def is_model_pulling(self, model: str, parameters: str) -> bool:
        container_name = f"{model}_{parameters}"
        container = self.get_container(container_name)
        if container is None or container.status != "running":
            return False
        return ContainerManager.is_pulling_model(container)

    def get_ollama_base_url(self, model: str, parameters: str) -> str | None:
        """The URL this server should use to reach the model's container.

        In Docker mode this server is itself a container on the same
        `chatbot-network` bridge, so it addresses the target directly by
        container name over Docker's internal DNS — no host port needed,
        and no `host.docker.internal`, which isn't resolvable on Linux
        Docker Engine without an `extra_hosts` entry docker-compose.yaml
        doesn't set (this breaks the whole app on Linux today).

        Outside Docker (`python manage.py runserver` on the host, container
        management still going through the Docker socket), there's no
        shared network to piggyback on, so it has to go through the
        allocated host-published port instead.
        """
        container_name = f"{model}_{parameters}"
        container = self.get_container(container_name)
        if container is None or container.status != "running":
            return None

        if os.getenv("DOCKER", "false") == "true":
            return f"http://{container_name}:11434"

        host_port = ContainerManager.get_container_environment_variable(container, "port")
        if host_port is None:
            return None
        return f"http://localhost:{host_port}"

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
        except docker.errors.APIError:
            # Container stopped between the caller's status check and this
            # call — not pulling if it's not even running.
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
