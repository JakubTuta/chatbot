"""refresh_catalog is the fix for the reported bug's root cause: the old
flow did `AIModel.objects.all().delete()` *before* scraping, so a parse
that (through no fault of its own) returned 0 models — which is exactly
what happened once ollama.com dropped the markup the old scraper keyed
off — wiped the entire catalog and, via CASCADE, every chat.

These tests assert the new rule holds: nothing is ever deleted unless a
*successful* parse proves it's gone, and even then only if it has no chat
history and (when checkable) no live container.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from container.ContainerManager import ContainerManager
from django_app import models
from django_app.catalog import sync
from django_app.catalog.parser import CatalogParseError, ParsedModel
from django_app.catalog.registry import VerifyResult

pytestmark = pytest.mark.django_db


def _parsed(name: str, variants=("8b",), popularity=1_000_000, capabilities=frozenset()) -> ParsedModel:
    return ParsedModel(
        name=name,
        description=f"{name} description",
        popularity=popularity,
        capabilities=capabilities,
        variants=variants,
    )


@pytest.fixture(autouse=True)
def _isolated_catalog(monkeypatch):
    # The 0004_seed_model_catalog migration pre-populates ~40 real models
    # (including "llama3.1") into every fresh test database, so a test
    # assuming an empty AIModel table would collide with seed data or have
    # prune sweep up rows it never created. Clear it so each test only ever
    # sees what it creates itself.
    models.AIModel.objects.all().delete()

    # Prune checks for a live container via the Docker SDK, and the
    # constructor itself dials a real Docker daemon unless a client is
    # already set — none of these tests should depend on, or wait on, a
    # real daemon being reachable. Individual tests override the return
    # value where the container-check branch itself is under test.
    monkeypatch.setattr(ContainerManager, "_client", MagicMock())
    monkeypatch.setattr(ContainerManager, "is_connected", lambda self: False)


def test_parse_failure_leaves_existing_catalog_untouched(monkeypatch):
    existing = models.AIModel.objects.create(name="llama3.1", model="llama3.1", index=1)

    monkeypatch.setattr(sync, "fetch_library_html", lambda: "<html></html>")
    monkeypatch.setattr(
        sync,
        "parse_library",
        lambda html: (_ for _ in ()).throw(CatalogParseError("0 models parsed")),
    )

    result = sync.refresh_catalog(min_pull_count=0)

    assert result.error == "0 models parsed"
    assert models.AIModel.objects.count() == 1
    assert models.AIModel.objects.get(pk=existing.pk).model == "llama3.1"


def test_network_failure_leaves_existing_catalog_untouched(monkeypatch):
    models.AIModel.objects.create(name="llama3.1", model="llama3.1", index=1)

    def _raise():
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(sync, "fetch_library_html", _raise)

    result = sync.refresh_catalog(min_pull_count=0)

    assert result.error is not None
    assert models.AIModel.objects.count() == 1


def test_successful_refresh_creates_model_and_verified_variant(monkeypatch):
    monkeypatch.setattr(sync, "fetch_library_html", lambda: "<html></html>")
    monkeypatch.setattr(sync, "parse_library", lambda html: [_parsed("llama3.1", variants=("8b",))])
    monkeypatch.setattr(
        sync.registry,
        "verify_tags",
        lambda names_and_tags, on_result=None: {
            ("llama3.1", "8b"): VerifyResult(status="ok", size_bytes=4_700_000_000)
        },
    )

    result = sync.refresh_catalog(min_pull_count=0)

    assert result.error is None
    assert result.created == 1
    assert result.variants_verified == 1

    ai_model = models.AIModel.objects.get(model="llama3.1")
    version = ai_model.versions.get(parameters="8b")
    assert version.size_bytes == 4_700_000_000


def test_refresh_persists_tools_capability(monkeypatch):
    monkeypatch.setattr(sync, "fetch_library_html", lambda: "<html></html>")
    monkeypatch.setattr(
        sync, "parse_library",
        lambda html: [_parsed("llama3.1", variants=("8b",), capabilities=frozenset({"tools"}))],
    )
    monkeypatch.setattr(
        sync.registry, "verify_tags",
        lambda names_and_tags, on_result=None: {
            ("llama3.1", "8b"): VerifyResult(status="ok", size_bytes=4_700_000_000)
        },
    )

    sync.refresh_catalog(min_pull_count=0)

    assert models.AIModel.objects.get(model="llama3.1").can_use_tools is True


def test_refresh_updates_tools_capability_on_existing_model(monkeypatch):
    models.AIModel.objects.create(name="llama3.1", model="llama3.1", can_use_tools=True, index=1)

    monkeypatch.setattr(sync, "fetch_library_html", lambda: "<html></html>")
    monkeypatch.setattr(
        sync, "parse_library",
        lambda html: [_parsed("llama3.1", variants=("8b",), capabilities=frozenset())],
    )
    monkeypatch.setattr(
        sync.registry, "verify_tags",
        lambda names_and_tags, on_result=None: {
            ("llama3.1", "8b"): VerifyResult(status="ok", size_bytes=4_700_000_000)
        },
    )

    sync.refresh_catalog(min_pull_count=0)

    assert models.AIModel.objects.get(model="llama3.1").can_use_tools is False


def test_below_min_pull_count_is_not_imported(monkeypatch):
    monkeypatch.setattr(sync, "fetch_library_html", lambda: "<html></html>")
    monkeypatch.setattr(
        sync, "parse_library", lambda html: [_parsed("obscure-model", popularity=10)]
    )
    monkeypatch.setattr(sync.registry, "verify_tags", lambda names_and_tags, on_result=None: {})

    result = sync.refresh_catalog(min_pull_count=1_000_000)

    assert result.created == 0
    assert not models.AIModel.objects.filter(model="obscure-model").exists()


def test_variant_verified_not_found_is_dropped_but_model_stays(monkeypatch):
    ai_model = models.AIModel.objects.create(name="llama3.1", model="llama3.1", index=1)
    models.AIModelVersion.objects.create(ai_model=ai_model, parameters="8b", size="4.4 GB")

    monkeypatch.setattr(sync, "fetch_library_html", lambda: "<html></html>")
    monkeypatch.setattr(sync, "parse_library", lambda html: [_parsed("llama3.1", variants=("8b",))])
    monkeypatch.setattr(
        sync.registry,
        "verify_tags",
        lambda names_and_tags, on_result=None: {("llama3.1", "8b"): VerifyResult(status="not_found")},
    )

    sync.refresh_catalog(min_pull_count=0)

    ai_model.refresh_from_db()
    assert not ai_model.versions.filter(parameters="8b").exists()


def test_prune_never_touches_a_model_with_chat_history(monkeypatch):
    ai_model = models.AIModel.objects.create(name="discontinued", model="discontinued", index=1)
    models.ChatHistory.objects.create(ai_model=ai_model, title="An old chat")

    monkeypatch.setattr(sync, "fetch_library_html", lambda: "<html></html>")
    # Model no longer appears on ollama.com at all.
    monkeypatch.setattr(sync, "parse_library", lambda html: [_parsed("some-other-model")])
    monkeypatch.setattr(sync.registry, "verify_tags", lambda names_and_tags, on_result=None: {})
    monkeypatch.setattr(ContainerManager, "is_connected", lambda self: True)
    monkeypatch.setattr(ContainerManager, "get_container", lambda self, name: None)

    result = sync.refresh_catalog(min_pull_count=0)

    assert result.pruned == 0
    assert models.AIModel.objects.filter(pk=ai_model.pk).exists()
    assert models.ChatHistory.objects.filter(ai_model=ai_model).exists()


def test_prune_removes_model_with_no_history_and_no_live_container(monkeypatch):
    ai_model = models.AIModel.objects.create(name="discontinued", model="discontinued", index=1)

    monkeypatch.setattr(sync, "fetch_library_html", lambda: "<html></html>")
    monkeypatch.setattr(sync, "parse_library", lambda html: [_parsed("some-other-model")])
    monkeypatch.setattr(sync.registry, "verify_tags", lambda names_and_tags, on_result=None: {})
    monkeypatch.setattr(ContainerManager, "is_connected", lambda self: True)
    monkeypatch.setattr(ContainerManager, "get_container", lambda self, name: None)

    result = sync.refresh_catalog(min_pull_count=0)

    assert result.pruned == 1
    assert not models.AIModel.objects.filter(pk=ai_model.pk).exists()


def test_prune_leaves_model_alone_when_docker_unreachable(monkeypatch):
    # Can't prove there's no live container right now — must not guess.
    ai_model = models.AIModel.objects.create(name="discontinued", model="discontinued", index=1)

    monkeypatch.setattr(sync, "fetch_library_html", lambda: "<html></html>")
    monkeypatch.setattr(sync, "parse_library", lambda html: [_parsed("some-other-model")])
    monkeypatch.setattr(sync.registry, "verify_tags", lambda names_and_tags, on_result=None: {})
    # _no_real_docker fixture already forces is_connected() False.

    result = sync.refresh_catalog(min_pull_count=0)

    assert result.pruned == 0
    assert models.AIModel.objects.filter(pk=ai_model.pk).exists()
