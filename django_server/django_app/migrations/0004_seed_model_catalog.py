import json
import pathlib

from django.db import migrations

FIXTURE_PATH = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "model_catalog.json"


def load_seed_catalog(apps, schema_editor):
    """Populate a fresh install with a working catalog and zero network
    calls, so the app is usable in the first five seconds instead of
    demanding a "Refresh model list" round-trip to ollama.com before a user
    can do anything. Uses get_or_create so re-running against a database
    that already has models (upgrades) never overwrites existing data.
    """
    AIModel = apps.get_model("django_app", "AIModel")
    AIModelVersion = apps.get_model("django_app", "AIModelVersion")

    with open(FIXTURE_PATH, encoding="utf-8") as f:
        seed_models = json.load(f)

    next_index = (AIModel.objects.order_by("-index").values_list("index", flat=True).first() or 0) + 1

    for entry in seed_models:
        ai_model, created = AIModel.objects.get_or_create(
            model=entry["model"],
            defaults={
                "name": entry["name"],
                "description": entry["description"],
                "popularity": entry["popularity"],
                "can_process_image": entry["can_process_image"],
                "is_embedding": entry["is_embedding"],
                "index": next_index,
            },
        )
        if created:
            next_index += 1

        for version in entry["versions"]:
            AIModelVersion.objects.get_or_create(
                ai_model=ai_model,
                parameters=version["parameters"],
                defaults={
                    "size": version["size"],
                    "size_bytes": version["size_bytes"],
                },
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("django_app", "0003_catalog_integrity"),
    ]

    operations = [
        migrations.RunPython(load_seed_catalog, noop),
    ]
