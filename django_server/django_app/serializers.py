import django_auth.serializers as auth_serializers
from rest_framework import serializers

from . import models


class AIModelVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AIModelVersion
        fields: list[str] = ["parameters", "size"]

    def create(self, validated_data) -> models.AIModelVersion:
        ai_model_version = models.AIModelVersion.objects.create(**validated_data)

        return ai_model_version


class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AIModel
        fields: list[str] = [
            "id",
            "name",
            "model",
            "description",
            "popularity",
            "can_process_image",
            "versions",
        ]

    def create(self, validated_data) -> models.AIModel:
        ai_model = models.AIModel.objects.create(**validated_data)

        return ai_model


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Message
        fields: list[str] = ["role", "content", "image"]

    def create(self, validated_data) -> models.Message:
        message = models.Message.objects.create(**validated_data)

        return message


class ChatHistorySerializer(serializers.ModelSerializer):
    ai_model = AIModelSerializer()
    user = auth_serializers.UserSerializer()

    class Meta:
        model = models.ChatHistory
        fields: list[str] = [
            "id",
            "user",
            "ai_model",
            "title",
            "last_update_time",
            "history",
        ]

    def create(self, validated_data) -> models.ChatHistory:
        chat_history = models.ChatHistory.objects.create(**validated_data)

        return chat_history
