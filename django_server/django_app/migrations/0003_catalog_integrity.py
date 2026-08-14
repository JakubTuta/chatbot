from django.db import migrations, models


def dedupe_ai_models(apps, schema_editor):
    """Merge AIModel rows that share the same `model` value (created by the
    old scraper's race-prone filter-then-create in views.py), then merge
    duplicate (ai_model, parameters) version rows. Needed before the unique
    constraints below can apply.
    """
    AIModel = apps.get_model("django_app", "AIModel")
    AIModelVersion = apps.get_model("django_app", "AIModelVersion")
    ChatHistory = apps.get_model("django_app", "ChatHistory")

    canonical_id_by_model: dict[str, int] = {}
    for ai_model in AIModel.objects.order_by("id"):
        canonical_id = canonical_id_by_model.get(ai_model.model)
        if canonical_id is None:
            canonical_id_by_model[ai_model.model] = ai_model.id
            continue

        AIModelVersion.objects.filter(ai_model_id=ai_model.id).update(ai_model_id=canonical_id)
        ChatHistory.objects.filter(ai_model_id=ai_model.id).update(ai_model_id=canonical_id)
        ai_model.delete()

    seen_versions: dict[tuple[int, str], int] = {}
    for version in AIModelVersion.objects.order_by("id"):
        key = (version.ai_model_id, version.parameters)
        if key not in seen_versions:
            seen_versions[key] = version.id
            continue
        version.delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("django_app", "0002_remove_chathistory_user"),
    ]

    operations = [
        migrations.RunPython(dedupe_ai_models, noop),
        migrations.AddField(
            model_name="aimodel",
            name="is_embedding",
            field=models.BooleanField(
                default=False,
                help_text="True for embedding-only models (e.g. nomic-embed-text). "
                "Excluded from the chat model picker; used for RAG.",
            ),
        ),
        migrations.AddField(
            model_name="aimodelversion",
            name="size_bytes",
            field=models.BigIntegerField(
                blank=True, null=True, help_text="Exact pull size from the registry manifest."
            ),
        ),
        migrations.AddField(
            model_name="aimodelversion",
            name="verified_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Last time this tag was confirmed pullable against registry.ollama.ai.",
            ),
        ),
        migrations.AlterField(
            model_name="aimodel",
            name="model",
            field=models.TextField(unique=True),
        ),
        migrations.AddConstraint(
            model_name="aimodelversion",
            constraint=models.UniqueConstraint(
                fields=("ai_model", "parameters"), name="unique_ai_model_version"
            ),
        ),
    ]
