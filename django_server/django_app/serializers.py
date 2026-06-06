from rest_framework import serializers

from . import models


class AIModelVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AIModelVersion
        fields: list[str] = ["parameters", "size"]


class AIModelSerializer(serializers.ModelSerializer):
    versions = AIModelVersionSerializer(many=True, read_only=True)

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
            "index",
        ]


class ChatHistorySerializer(serializers.ModelSerializer):
    ai_model = AIModelSerializer(read_only=True)

    class Meta:
        model = models.ChatHistory
        fields = [
            "id",
            "ai_model",
            "title",
            "last_update_time",
        ]

    def create(self, validated_data):
        ai_model = self.context.get("ai_model")

        validated_data["ai_model"] = ai_model

        return models.ChatHistory.objects.create(**validated_data)
