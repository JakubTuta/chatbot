from django.contrib.auth.models import User
from djongo import models

# Create your models here.


class AIModel(models.Model):
    name = models.TextField()
    model = models.TextField()

    def __str__(self):
        return self.name


class Message(models.Model):
    role = models.TextField()
    content = models.TextField()

    def __str__(self):
        return f"{self.role}: {self.content}"


class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    title = models.TextField(default="New chat")
    last_update_time = models.DateTimeField(auto_now=True)
    history = models.ArrayModelField(
        model_container=Message,
    )

    def __str__(self):
        return self.title
