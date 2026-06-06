import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name="AIModel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.TextField()),
                ("model", models.TextField()),
                ("description", models.TextField()),
                ("popularity", models.IntegerField(default=0)),
                ("can_process_image", models.BooleanField(default=False)),
                ("index", models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="AIModelVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("parameters", models.TextField()),
                ("size", models.TextField()),
                ("ai_model", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="django_app.aimodel")),
            ],
        ),
        migrations.CreateModel(
            name="ChatHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.TextField(default="New chat")),
                ("last_update_time", models.DateTimeField(auto_now=True)),
                ("ai_model", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="django_app.aimodel")),
            ],
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.TextField()),
                ("content", models.TextField()),
                ("image", models.TextField(default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("chat", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="django_app.chathistory")),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
