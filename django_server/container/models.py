from django.db import models


class ContainerPort(models.Model):
    """Stable host-port allocation for an Ollama container.

    Replaces `11434 + ai_model.index`: `index` is renumbered on every
    catalog refresh and has no uniqueness constraint, so two different
    models could compute the same host port. When that happened,
    `close_any_container_on_port` would stop whichever container was
    already listening there — silently killing an unrelated live chat.
    A port allocated here is never reused for a different container.
    """

    container_name = models.TextField(unique=True)
    port = models.IntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.container_name} -> {self.port}"
