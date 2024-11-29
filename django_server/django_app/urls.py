from django.urls import path
from django.urls.resolvers import URLPattern

from . import views

urlpatterns: list[URLPattern] = [
    path(
        "chat-history/<str:model>/<str:chat_id>",
        views.ChatHistory.as_view(),
        name="chat_history",
    ),
    path("all-chats/<str:model>", views.AllChats.as_view(), name="all_chats"),
    path("ai-models/", views.AIModels.as_view(), name="ai_models"),
    path("ask-bot/<str:model>/<str:chat_id>", views.AskBot.as_view(), name="ask_bot"),
]
