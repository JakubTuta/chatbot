from django.contrib.auth.models import User
from djongo import models

# Create your models here.


class AIModelVersion(models.Model):
    parameters = models.TextField()
    size = models.TextField()


class AIModel(models.Model):
    id = models.ObjectIdField()
    name = models.TextField()
    model = models.TextField()
    description = models.TextField()
    popularity = models.IntegerField(default=0)
    can_process_image = models.BooleanField(default=False)
    versions = models.ArrayModelField(model_container=AIModelVersion)


class Message(models.Model):
    role = models.TextField()
    content = models.TextField()
    image = models.TextField(default="")


class ChatHistory(models.Model):
    id = models.ObjectIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    title = models.TextField(default="New chat")
    last_update_time = models.DateTimeField(auto_now=True)
    history = models.ArrayModelField(
        model_container=Message,
    )
