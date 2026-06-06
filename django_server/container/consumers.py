import json
import logging
import threading
import time

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

_snapshot_thread_started = False
_snapshot_thread_lock = threading.Lock()


def _start_snapshot_thread() -> None:
    global _snapshot_thread_started
    with _snapshot_thread_lock:
        if _snapshot_thread_started:
            return
        _snapshot_thread_started = True

    def _run() -> None:
        while True:
            time.sleep(2)
            try:
                from container.ContainerManager import ContainerManager
                from django_app import progress_state

                docker_client = ContainerManager()
                containers = docker_client.get_available_containers()
                snapshot = progress_state.get_snapshot()
                channel_layer = get_channel_layer()
                if channel_layer is None:
                    continue
                async_to_sync(channel_layer.group_send)(
                    "container_status",
                    {
                        "type": "snapshot",
                        "payload": {
                            "type": "snapshot",
                            "containers": containers,
                            **snapshot,
                        },
                    },
                )
            except Exception as e:
                logger.debug("Snapshot thread error: %s", e)

    t = threading.Thread(target=_run, daemon=True, name="container-snapshot")
    t.start()


class ContainerStatusConsumer(WebsocketConsumer):
    def connect(self) -> None:
        async_to_sync(self.channel_layer.group_add)(  # type: ignore
            "container_status", self.channel_name
        )
        self.accept()
        _start_snapshot_thread()
        self._send_snapshot()

    def disconnect(self, code: int) -> None:
        async_to_sync(self.channel_layer.group_discard)(  # type: ignore
            "container_status", self.channel_name
        )

    def _send_snapshot(self) -> None:
        try:
            from container.ContainerManager import ContainerManager
            from django_app import progress_state

            docker_client = ContainerManager()
            containers = docker_client.get_available_containers()
            snapshot = progress_state.get_snapshot()
            self.send(
                text_data=json.dumps(
                    {
                        "type": "snapshot",
                        "containers": containers,
                        **snapshot,
                    }
                )
            )
        except Exception as e:
            logger.warning("Failed to send initial snapshot: %s", e)

    def _relay(self, event: dict) -> None:
        try:
            self.send(text_data=json.dumps(event["payload"]))
        except Exception as e:
            logger.debug("Relay error: %s", e)

    def container_update(self, event: dict) -> None:
        self._relay(event)

    def image_pull_progress(self, event: dict) -> None:
        self._relay(event)

    def model_pull_progress(self, event: dict) -> None:
        self._relay(event)

    def scrape_progress(self, event: dict) -> None:
        self._relay(event)

    def snapshot(self, event: dict) -> None:
        self._relay(event)
