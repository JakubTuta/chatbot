"""ContainerManager owns two behaviours that used to be silently wrong:

* the Docker client was constructed per-instance (a `self.__client` name-
  mangling bug defeated the intended class-level singleton), leaking a
  connection on every chat message, every 2s snapshot tick, and every view;
* `pull_model_with_progress` never checked Ollama's own `{"error": ...}`
  event, so a bad tag still drove the progress bar to 100% and reported
  "Model ready" — verified against real behaviour: `/api/pull` streams
  errors under HTTP 200, it never raises on its own.

These tests exercise both against a mocked Docker SDK / mocked `requests`,
never a real daemon.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import docker.errors
import pytest
import requests

from container import ContainerManager as container_manager_module
from container.ContainerManager import PORT_RANGE_START, ContainerManager
from container.models import ContainerPort


@pytest.fixture(autouse=True)
def _reset_singleton(monkeypatch):
    monkeypatch.setattr(ContainerManager, "_client", None)


def test_client_is_a_singleton_across_instances(monkeypatch):
    fake_clients = []

    def _fake_docker_client():
        client = MagicMock()
        fake_clients.append(client)
        return client

    monkeypatch.setattr(container_manager_module.docker, "DockerClient", _fake_docker_client)

    ContainerManager()
    ContainerManager()
    ContainerManager()

    assert len(fake_clients) == 1


def test_is_connected_false_before_any_connection(monkeypatch):
    def _raise():
        raise docker.errors.DockerException("no daemon")

    monkeypatch.setattr(container_manager_module.docker, "DockerClient", _raise)

    manager = ContainerManager()

    assert manager.is_connected() is False


def test_is_connected_drops_client_after_failed_ping(monkeypatch):
    stale_client = MagicMock()
    stale_client.ping.side_effect = docker.errors.APIError("daemon gone")
    monkeypatch.setattr(ContainerManager, "_client", stale_client)

    manager = ContainerManager.__new__(ContainerManager)

    assert manager.is_connected() is False
    assert ContainerManager._client is None


def test_is_connected_true_on_successful_ping(monkeypatch):
    live_client = MagicMock()
    live_client.ping.return_value = True
    monkeypatch.setattr(ContainerManager, "_client", live_client)

    manager = ContainerManager.__new__(ContainerManager)

    assert manager.is_connected() is True


@pytest.mark.django_db
def test_allocate_port_reuses_existing_allocation():
    first = ContainerManager.allocate_port("llama3.1_8b")
    second = ContainerManager.allocate_port("llama3.1_8b")

    assert first == second
    assert ContainerPort.objects.filter(container_name="llama3.1_8b").count() == 1


@pytest.mark.django_db
def test_allocate_port_gives_different_containers_different_ports():
    first = ContainerManager.allocate_port("llama3.1_8b")
    second = ContainerManager.allocate_port("llama3.1_70b")

    assert first != second
    assert first >= PORT_RANGE_START
    assert second >= PORT_RANGE_START


@pytest.mark.django_db
def test_allocate_port_skips_ports_already_taken():
    ContainerPort.objects.create(container_name="other_model_8b", port=PORT_RANGE_START)

    port = ContainerManager.allocate_port("llama3.1_8b")

    assert port != PORT_RANGE_START


class _FakeStreamResponse:
    def __init__(self, lines: list[bytes]):
        self._lines = lines

    def raise_for_status(self):
        pass

    def iter_lines(self):
        return iter(self._lines)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_pull_model_with_progress_reports_failure_on_stream_error(monkeypatch):
    lines = [
        json.dumps({"status": "pulling manifest"}).encode(),
        json.dumps({"error": "pull model manifest: file does not exist"}).encode(),
    ]
    monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeStreamResponse(lines))

    manager = ContainerManager.__new__(ContainerManager)
    success, error = manager.pull_model_with_progress("bogus-model", "8b", "http://localhost:11434")

    assert success is False
    assert error == "pull model manifest: file does not exist"


def test_pull_model_with_progress_reports_success_and_final_progress(monkeypatch):
    lines = [
        json.dumps({"status": "pulling layer", "digest": "sha256:abc", "total": 100, "completed": 50}).encode(),
        json.dumps({"status": "pulling layer", "digest": "sha256:abc", "total": 100, "completed": 100}).encode(),
        json.dumps({"status": "success"}).encode(),
    ]
    monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeStreamResponse(lines))

    progress_calls: list[tuple[int, str]] = []
    manager = ContainerManager.__new__(ContainerManager)
    success, error = manager.pull_model_with_progress(
        "llama3.1", "8b", "http://localhost:11434", progress_cb=lambda pct, detail: progress_calls.append((pct, detail))
    )

    assert success is True
    assert error is None
    assert progress_calls[-1] == (100, "Model ready")
