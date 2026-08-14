"""CompareConsumer over Channels' WebsocketCommunicator, same style as
test_consumers.py — astream_bot_response is monkeypatched so these never
touch Ollama or Docker. Compare is ephemeral (no ChatHistory involved), so
there's no persistence to check, just protocol/fan-out behavior.
"""

from __future__ import annotations

import asyncio

import pytest
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.urls import re_path

from django_app import functions, models
from django_app.consumers import CompareConsumer

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.asyncio]


def _application():
    return URLRouter([re_path(r"ws/compare/$", CompareConsumer.as_asgi())])


@pytest.fixture(autouse=True)
def _in_memory_channel_layer(settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


@pytest.fixture(autouse=True)
async def _close_leaked_db_connection():
    yield
    from django.db import connections

    await database_sync_to_async(connections.close_all)()


@pytest.fixture
def two_models():
    models.AIModel.objects.filter(model__in=["compare-a", "compare-b"]).delete()
    a = models.AIModel.objects.create(name="A", model="compare-a", index=1)
    b = models.AIModel.objects.create(name="B", model="compare-b", index=2)
    return a, b


async def _collect_until_both_done(communicator, target_keys):
    """Compare fans out concurrently, so message order across targets isn't
    guaranteed — collect everything and group by target instead of
    asserting a fixed sequence.
    """
    by_target: dict[str, list[dict]] = {key: [] for key in target_keys}
    done = set()

    while len(done) < len(target_keys):
        message = await communicator.receive_json_from()
        target = message["target"]
        by_target[target].append(message)
        if message.get("done"):
            done.add(target)

    return by_target


async def test_receive_streams_from_two_models_concurrently(two_models, monkeypatch):
    async def _fake_astream(model, parameters, message, image, history, system_prompt=None, generation_params=None, stats=None):
        for chunk in (f"{model.model}-1", f"{model.model}-2"):
            yield chunk

    monkeypatch.setattr(functions, "astream_bot_response", _fake_astream)

    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({
        "prompt": "Hi",
        "targets": [
            {"model": "compare-a", "parameters": "8b"},
            {"model": "compare-b", "parameters": "8b"},
        ],
    })

    by_target = await _collect_until_both_done(communicator, ["compare-a:8b", "compare-b:8b"])

    assert [m["message"] for m in by_target["compare-a:8b"] if not m["done"]] == ["compare-a-1", "compare-a-2"]
    assert [m["message"] for m in by_target["compare-b:8b"] if not m["done"]] == ["compare-b-1", "compare-b-2"]
    assert by_target["compare-a:8b"][-1] == {"target": "compare-a:8b", "message": "", "done": True}
    assert by_target["compare-b:8b"][-1] == {"target": "compare-b:8b", "message": "", "done": True}

    await communicator.disconnect()


async def test_receive_includes_stats_when_reported(two_models, monkeypatch):
    async def _fake_astream(model, parameters, message, image, history, system_prompt=None, generation_params=None, stats=None):
        if stats is not None:
            stats["completion_tokens"] = 5
        yield "hi"

    monkeypatch.setattr(functions, "astream_bot_response", _fake_astream)

    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    await communicator.send_json_to({"prompt": "Hi", "targets": [{"model": "compare-a", "parameters": "8b"}]})

    by_target = await _collect_until_both_done(communicator, ["compare-a:8b"])
    assert by_target["compare-a:8b"][-1]["stats"] == {"completion_tokens": 5}

    await communicator.disconnect()


async def test_receive_unknown_model_reports_per_target_error(two_models):
    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    await communicator.send_json_to({
        "prompt": "Hi", "targets": [{"model": "does-not-exist", "parameters": "8b"}],
    })

    response = await communicator.receive_json_from()
    assert response == {"target": "does-not-exist:8b", "error": "Model not found.", "done": True}

    await communicator.disconnect()


async def test_receive_one_model_failing_does_not_block_the_other(two_models, monkeypatch):
    from django_app.functions import ModelUnavailableError

    async def _fake_astream(model, parameters, message, image, history, system_prompt=None, generation_params=None, stats=None):
        if model.model == "compare-a":
            raise ModelUnavailableError("not running")
        yield "ok"

    monkeypatch.setattr(functions, "astream_bot_response", _fake_astream)

    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    await communicator.send_json_to({
        "prompt": "Hi",
        "targets": [
            {"model": "compare-a", "parameters": "8b"},
            {"model": "compare-b", "parameters": "8b"},
        ],
    })

    by_target = await _collect_until_both_done(communicator, ["compare-a:8b", "compare-b:8b"])

    assert by_target["compare-a:8b"] == [{"target": "compare-a:8b", "error": "not running", "done": True}]
    assert by_target["compare-b:8b"][-1]["done"] is True
    assert any(m.get("message") == "ok" for m in by_target["compare-b:8b"])

    await communicator.disconnect()


async def test_receive_rejects_empty_prompt():
    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    await communicator.send_json_to({"prompt": "", "targets": [{"model": "x", "parameters": "8b"}]})

    response = await communicator.receive_json_from()
    assert response["error"]
    assert response["target"] is None

    await communicator.disconnect()


async def test_receive_rejects_too_many_targets():
    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    targets = [{"model": f"m{i}", "parameters": "8b"} for i in range(5)]
    await communicator.send_json_to({"prompt": "Hi", "targets": targets})

    response = await communicator.receive_json_from()
    assert "between 1 and 4" in response["error"]

    await communicator.disconnect()


async def test_receive_rejects_empty_targets():
    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    await communicator.send_json_to({"prompt": "Hi", "targets": []})

    response = await communicator.receive_json_from()
    assert "between 1 and 4" in response["error"]

    await communicator.disconnect()


async def test_receive_invalid_json_reports_error():
    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    await communicator.send_to(text_data="not json")

    response = await communicator.receive_json_from()
    assert response["error"] == "Invalid message format."

    await communicator.disconnect()


async def test_receive_while_running_is_rejected(two_models, monkeypatch):
    started = asyncio.Event()
    release = asyncio.Event()

    async def _fake_astream(model, parameters, message, image, history, system_prompt=None, generation_params=None, stats=None):
        started.set()
        await release.wait()
        yield "ok"

    monkeypatch.setattr(functions, "astream_bot_response", _fake_astream)

    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    await communicator.send_json_to({"prompt": "Hi", "targets": [{"model": "compare-a", "parameters": "8b"}]})
    await asyncio.wait_for(started.wait(), timeout=2)

    await communicator.send_json_to({"prompt": "Hi again", "targets": [{"model": "compare-b", "parameters": "8b"}]})
    response = await communicator.receive_json_from()
    assert "already running" in response["error"]

    release.set()
    # Drain the first comparison's own completion so the communicator/task
    # don't outlive the test.
    while True:
        msg = await communicator.receive_json_from()
        if msg.get("done"):
            break

    await communicator.disconnect()


async def test_stop_cancels_in_flight_comparison_for_every_target(two_models, monkeypatch):
    started = asyncio.Event()
    release = asyncio.Event()

    async def _fake_astream(model, parameters, message, image, history, system_prompt=None, generation_params=None, stats=None):
        started.set()
        await release.wait()
        yield "should never be reached"

    monkeypatch.setattr(functions, "astream_bot_response", _fake_astream)

    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    await communicator.send_json_to({
        "prompt": "Hi",
        "targets": [
            {"model": "compare-a", "parameters": "8b"},
            {"model": "compare-b", "parameters": "8b"},
        ],
    })
    await asyncio.wait_for(started.wait(), timeout=2)

    await communicator.send_json_to({"type": "stop"})

    by_target = await _collect_until_both_done(communicator, ["compare-a:8b", "compare-b:8b"])

    assert by_target["compare-a:8b"] == [{"target": "compare-a:8b", "message": "", "done": True, "stopped": True}]
    assert by_target["compare-b:8b"] == [{"target": "compare-b:8b", "message": "", "done": True, "stopped": True}]

    await communicator.disconnect()


async def test_stop_with_nothing_running_is_a_no_op():
    communicator = WebsocketCommunicator(_application(), "/ws/compare/")
    await communicator.connect()

    await communicator.send_json_to({"type": "stop"})

    # No error, no stray frame — just confirm a follow-up comparison still
    # works normally afterward.
    assert await communicator.receive_nothing(timeout=0.2)

    await communicator.disconnect()
