# Generated by Django 4.1.13 on 2024-11-23 19:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_app.models
import djongo.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AIModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('model', models.TextField()),
                ('description', models.TextField()),
                ('can_process_image', models.BooleanField(default=False)),
                ('versions', djongo.models.fields.ArrayModelField(model_container=django_app.models.AIModelVersion)),
            ],
        ),
        migrations.CreateModel(
            name='AIModelVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parameters', models.TextField()),
                ('size', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.TextField()),
                ('content', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='ChatHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(default='New chat')),
                ('last_update_time', models.DateTimeField(auto_now=True)),
                ('history', djongo.models.fields.ArrayModelField(model_container=django_app.models.Message)),
                ('ai_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_app.aimodel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
