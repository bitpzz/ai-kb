from django.db import models
from django.contrib.auth.models import User
import uuid


class KnowledgeBase(models.Model):
    """A user's knowledge base — a collection of documents."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="knowledge_bases"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class Document(models.Model):
    """A document uploaded to a knowledge base."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kb = models.ForeignKey(
        KnowledgeBase, on_delete=models.CASCADE, related_name="documents"
    )
    filename = models.CharField(max_length=500)
    file_type = models.CharField(max_length=50)  # pdf, docx, txt
    file_size = models.IntegerField(default=0)  # bytes
    file = models.FileField(upload_to="documents/%Y/%m/")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    content_text = models.TextField(blank=True, default="")
    chunk_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.filename


class Conversation(models.Model):
    """A conversation within a knowledge base."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kb = models.ForeignKey(
        KnowledgeBase, on_delete=models.CASCADE, related_name="conversations"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="conversations"
    )
    title = models.CharField(max_length=500, blank=True, default="新的对话")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Conversation {self.id}"


class Message(models.Model):
    """A single message in a conversation."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    # sources: [{"content": "...", "filename": "...", "chunk_index": 0}, ...]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
