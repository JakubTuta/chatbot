import requests
from django.contrib.auth.models import User
from django.http import QueryDict

base_url = "http://localhost:8000"


def find_user(username: str) -> User | None:
    return User.objects.filter(username=username).first()


def check_if_password_correct(user: User, password: str) -> bool:
    return user.check_password(password)


def get_jwt_token(username: str, password: str) -> dict[str, str]:
    url = f"{base_url}/auth/token/"

    data: dict[str, str] = {
        "username": username,
        "password": password,
    }

    response: requests.Response = requests.post(url, data=data)

    return response.json()


def refresh_token(token: str) -> str | None:
    url = f"{base_url}/auth/token/refresh/"

    data: dict[str, str] = {
        "refresh": token,
    }

    response: requests.Response = requests.post(url, data=data)

    if response.status_code != 200:
        return None

    access_token: str = response.json()["access"]

    return access_token


def verify_token(token: str) -> bool:
    url = f"{base_url}/auth/token/verify/"

    data: dict[str, str] = {
        "token": token,
    }

    response: requests.Response = requests.post(url, data=data)

    return response.status_code == 200
