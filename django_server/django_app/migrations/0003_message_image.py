# Generated by Django 4.1.13 on 2024-12-09 01:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_app', '0002_aimodel_popularity'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='image',
            field=models.TextField(default=''),
        ),
    ]
