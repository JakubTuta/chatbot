import typing

from helpers import decorators
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from . import functions, serializers


class Login(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @decorators.required_body_params(["username", "password"])
    def post(self, request: Request) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore
        username = request_data["username"]
        password = request_data["password"]

        if (user := functions.find_user(username)) is None:
            return Response(
                {"error": "Username not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not functions.check_if_password_correct(user, password):
            return Response(
                {"error": "Incorrect password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token: dict[str, str] = functions.get_jwt_token(username, password)

        serializer = serializers.UserSerializer(user)

        return Response(
            {
                "user": serializer.data,
                "token": token,
            },
            status=status.HTTP_200_OK,
        )


class Register(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @decorators.required_body_params(["username", "password"])
    def post(self, request: Request) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore
        username = request_data["username"]
        password = request_data["password"]

        if functions.find_user(username) is not None:
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = serializers.UserSerializer(data=request_data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        token: dict[str, str] = functions.get_jwt_token(username, password)

        return Response(
            {
                "user": serializer.data,
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )


class UserMe(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if (user := functions.find_user(request.user.username)) is None:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = serializers.UserSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)


class CheckAndRefreshToken(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @decorators.required_body_params(["access", "refresh"])
    def post(self, request: Request) -> Response:
        request_data: dict[str, str] = request.data  # type: ignore
        access_token = request_data["access"]
        refresh_token = request_data["refresh"]

        if functions.verify_token(access_token):
            return Response(
                {
                    "token": {
                        "access": access_token,
                        "refresh": refresh_token,
                    },
                },
                status=status.HTTP_200_OK,
            )

        if (
            not functions.verify_token(refresh_token)
            or (new_access_token := functions.refresh_token(refresh_token)) is None
        ):
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "token": {
                    "access": new_access_token,
                    "refresh": refresh_token,
                },
            },
            status=status.HTTP_200_OK,
        )
