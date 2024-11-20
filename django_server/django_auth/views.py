import typing

from django.http import HttpRequest
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import functions, serializers


class Login(APIView):
    authentication_classes: list[typing.Any] = []
    permission_classes: list[type[AllowAny]] = [AllowAny]

    def post(self, request: HttpRequest) -> Response:
        # url: /auth/login/

        required_fields: list[str] = ["username", "password"]
        if missing_fields := functions.check_required_fields(
            request.data, required_fields  # type: ignore
        ):
            return Response(
                {"Error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username: str = request.data["username"]  # type: ignore
        password: str = request.data["password"]  # type: ignore

        if (user := functions.find_user(username)) is None:
            return Response(
                {"Error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not functions.check_if_password_correct(user, password):
            return Response(
                {"Error": "Invalid password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token: dict[str, str] = functions.get_jwt_token(username, password)

        serializer = serializers.UserSerializer(user)

        return Response(
            {
                "Status": "Success",
                "user": serializer.data,
                "token": token,
            },
            status=status.HTTP_200_OK,
        )


class Register(APIView):
    authentication_classes: list[typing.Any] = []
    permission_classes: list[type[AllowAny]] = [AllowAny]

    def post(self, request: HttpRequest) -> Response:
        # url: /auth/register/

        required_fields: list[str] = ["username", "password"]
        if missing_fields := functions.check_required_fields(
            request.data, required_fields  # type: ignore
        ):
            return Response(
                {"Error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username: str = request.data["username"]  # type: ignore
        password: str = request.data["password"]  # type: ignore

        serializer = serializers.UserSerializer(data=request.data)  # type: ignore

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        token: dict[str, str] = functions.get_jwt_token(username, password)

        return Response(
            {
                "Status": "Success",
                "user": serializer.data,
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )


class CheckAndRefreshToken(APIView):
    authentication_classes: list[typing.Any] = []
    permission_classes: list[type[AllowAny]] = [AllowAny]

    def post(self, request: HttpRequest) -> Response:
        # url: /auth/token/check-and-refresh/

        required_fields: list[str] = ["access", "refresh"]
        if missing_fields := functions.check_required_fields(
            request.data, required_fields  # type: ignore
        ):
            return Response(
                {"Error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token: str = request.data["access"]  # type: ignore
        refresh_token: str = request.data["refresh"]  # type: ignore

        if functions.verify_token(access_token):
            return Response(
                {
                    "Status": "Verified",
                    "token": {"access": access_token, "refresh": refresh_token},
                },
                status=status.HTTP_200_OK,
            )

        if (
            functions.verify_token(refresh_token)
            and (new_access_token := functions.refresh_token(refresh_token)) is not None
        ):
            return Response(
                {
                    "Status": "Refreshed",
                    "token": {"access": new_access_token, "refresh": refresh_token},
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"Error": "Invalid token"},
            status=status.HTTP_400_BAD_REQUEST,
        )
