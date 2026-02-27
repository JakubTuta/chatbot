from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)


def find_user(username: str) -> User | None:
    return User.objects.filter(username=username).first()


def check_if_password_correct(user: User, password: str) -> bool:
    return user.check_password(password)


def get_jwt_token(username: str, password: str) -> dict[str, str]:
    serializer = TokenObtainPairSerializer(data={
        "username": username,
        "password": password,
    })
    serializer.is_valid(raise_exception=True)

    return dict(serializer.validated_data)


def refresh_token(token: str) -> str | None:
    serializer = TokenRefreshSerializer(data={"refresh": token})

    try:
        serializer.is_valid(raise_exception=True)
        return str(serializer.validated_data["access"])
    except Exception:
        return None


def verify_token(token: str) -> bool:
    serializer = TokenVerifySerializer(data={"token": token})

    try:
        serializer.is_valid(raise_exception=True)
        return True
    except Exception:
        return False
