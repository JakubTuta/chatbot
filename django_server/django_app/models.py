from django.db import models


class AIModel(models.Model):
    name = models.TextField()
    model = models.TextField()
    description = models.TextField()
    popularity = models.IntegerField(default=0)
    can_process_image = models.BooleanField(default=False)
    index = models.IntegerField(default=0)


class AIModelVersion(models.Model):
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name="versions")
    parameters = models.TextField()
    size = models.TextField()


class ChatHistory(models.Model):
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    title = models.TextField(default="New chat")
    last_update_time = models.DateTimeField(auto_now=True)


class ChatMessage(models.Model):
    chat = models.ForeignKey(ChatHistory, on_delete=models.CASCADE, related_name="messages")
    role = models.TextField()
    content = models.TextField()
    image = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
