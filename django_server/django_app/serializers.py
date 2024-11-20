import django_auth.serializers as auth_serializers
from rest_framework import serializers

from . import models


class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AIModel
        fields: list[str] = ["id", "name", "model"]

    def create(self, validated_data) -> models.AIModel:
        ai_model = models.AIModel.objects.create(**validated_data)

        return ai_model


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Message
        fields: list[str] = ["role", "content"]

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
