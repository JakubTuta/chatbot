from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields: list[str] = ["id", "username", "password"]
        # extra_kwargs: dict[str, dict[str, bool]] = {"password": {"write_only": True}}

    def create(self, validated_data) -> User:
        user: User = User.objects.create_user(**validated_data)

        return user
