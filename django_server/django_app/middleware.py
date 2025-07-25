from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser, User
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user(token_key):
    try:
        access_token = AccessToken(token_key)
        user_id = access_token["user_id"]

        return User.objects.get(id=user_id)

    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_params = dict(
            x.split("=") for x in scope["query_string"].decode().split("&") if x
        )
        token = query_params.get("token", None)

        headers = dict(scope["headers"])
        if b"authorization" in headers:
            auth_header = headers[b"authorization"].decode()

            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if token:
            scope["user"] = await get_user(token)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(inner)
