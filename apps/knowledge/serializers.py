from rest_framework import serializers
from .models import KnowledgeBase, Document, Conversation, Message


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeBase
        fields = (
            "id", "name", "description", "document_count",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "document_count", "created_at", "updated_at")

    def get_document_count(self, obj):
        return obj.documents.count()


class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Document
        fields = (
            "id", "file", "filename", "file_type", "file_size",
            "status", "chunk_count", "error_message", "created_at",
        )
        read_only_fields = (
            "id", "filename", "file_type", "file_size", "status",
            "chunk_count", "error_message", "created_at",
        )


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "role", "content", "sources", "created_at")
        read_only_fields = ("id", "created_at")


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "title", "message_count", "messages", "created_at")
        read_only_fields = ("id", "created_at")

    def get_message_count(self, obj):
        return obj.messages.count()


class ConversationListSerializer(serializers.ModelSerializer):
    """Lighter serializer for conversation list (no messages)."""
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "title", "message_count", "created_at")
        read_only_fields = ("id", "created_at")

    def get_message_count(self, obj):
        return obj.messages.count()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, max_length=10000)
