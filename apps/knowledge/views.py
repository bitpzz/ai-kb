from rest_framework import generics, permissions, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import KnowledgeBase, Document, Conversation, Message
from .serializers import (
    KnowledgeBaseSerializer,
    DocumentSerializer,
    ConversationSerializer,
    ConversationListSerializer,
    ChatRequestSerializer,
    MessageSerializer,
)
from .rag.engine import process_document_task, remove_document_chunks, delete_collection
from .rag.chat import retrieve, create_sse_response
import threading


# ── KnowledgeBase CRUD ────────────────────────────────────────────

class KBListCreateView(generics.ListCreateAPIView):
    """GET /api/knowledge-bases/ — list | POST /api/knowledge-bases/ — create"""

    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return KnowledgeBase.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class KBRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/knowledge-bases/<id>/"""

    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return KnowledgeBase.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        """Cascade: delete ChromaDB collection, documents files, then KB."""
        delete_collection(str(instance.id))
        for doc in instance.documents.all():
            doc.file.delete(save=False)
        instance.delete()


# ── Documents ─────────────────────────────────────────────────────

class DocumentListCreateView(generics.ListCreateAPIView):
    """GET /api/knowledge-bases/<kb_id>/documents/ — list
       POST /api/knowledge-bases/<kb_id>/documents/ — upload"""

    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        kb_id = self.kwargs["kb_id"]
        return Document.objects.filter(kb_id=kb_id, kb__user=self.request.user)

    def perform_create(self, serializer):
        kb = get_object_or_404(
            KnowledgeBase, id=self.kwargs["kb_id"], user=self.request.user
        )
        uploaded = self.request.FILES.get("file")
        if uploaded:
            doc = serializer.save(
                kb=kb,
                filename=uploaded.name,
                file_type=uploaded.name.rsplit(".", 1)[-1].lower()
                if "." in uploaded.name
                else "txt",
                file_size=uploaded.size,
            )
            # Enqueue async processing task via thread (simpler than django-q for MVP)
            threading.Thread(
                target=process_document_task,
                args=(str(doc.id),),
                daemon=True,
            ).start()


class DocumentDestroyView(generics.DestroyAPIView):
    """DELETE /api/documents/<id>/"""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(kb__user=self.request.user)

    def perform_destroy(self, instance):
        """Remove ChromaDB chunks, delete file, then delete DB record."""
        remove_document_chunks(str(instance.kb_id), str(instance.id))
        instance.file.delete(save=False)
        instance.delete()


# ── Conversations ─────────────────────────────────────────────────

class ConversationListCreateView(generics.ListCreateAPIView):
    """GET /api/knowledge-bases/<kb_id>/conversations/ — list
       POST /api/knowledge-bases/<kb_id>/conversations/ — create"""

    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        kb_id = self.kwargs["kb_id"]
        return Conversation.objects.filter(kb_id=kb_id, user=self.request.user)

    def perform_create(self, serializer):
        kb = get_object_or_404(
            KnowledgeBase, id=self.kwargs["kb_id"], user=self.request.user
        )
        serializer.save(kb=kb, user=self.request.user)


class ConversationDetailView(generics.RetrieveDestroyAPIView):
    """GET/DELETE /api/conversations/<id>/"""

    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


# ── Chat (RAG-powered SSE streaming) ──────────────────────────────

class ChatView(generics.GenericAPIView):
    """POST /api/knowledge-bases/<kb_id>/chat/ — new conversation + SSE stream reply."""

    serializer_class = ChatRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, kb_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        kb = get_object_or_404(KnowledgeBase, id=kb_id, user=request.user)
        user_message = serializer.validated_data["message"]

        # Create conversation
        conv = Conversation.objects.create(
            kb=kb,
            user=request.user,
            title=user_message[:50],
        )

        # Save user message
        Message.objects.create(
            conversation=conv,
            role=Message.Role.USER,
            content=user_message,
        )

        # Retrieve relevant document chunks
        sources = retrieve(str(kb_id), user_message)

        # Stream assistant reply
        response = create_sse_response(user_message, sources)

        # Save the assistant message after streaming
        # (The stream captures the full response text, but for simplicity
        # we save via a SSE event handler on the frontend.
        # Here we add a header so the frontend knows the conversation ID.)
        response["X-Conversation-Id"] = str(conv.id)

        return response


class ContinueChatView(generics.GenericAPIView):
    """POST /api/conversations/<conv_id>/chat/ — continue + SSE stream reply."""

    serializer_class = ChatRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conv_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conv = get_object_or_404(Conversation, id=conv_id, user=request.user)
        user_message = serializer.validated_data["message"]

        # Save user message
        Message.objects.create(
            conversation=conv,
            role=Message.Role.USER,
            content=user_message,
        )

        # Retrieve relevant document chunks
        sources = retrieve(str(conv.kb_id), user_message)

        # Stream assistant reply
        response = create_sse_response(user_message, sources)
        response["X-Conversation-Id"] = str(conv.id)

        return response


# Add MessagesList view for fetching conversation messages
class MessagesListView(generics.ListAPIView):
    """GET /api/conversations/<conv_id>/messages/"""

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conv_id = self.kwargs["conv_id"]
        return Message.objects.filter(
            conversation_id=conv_id, conversation__user=self.request.user
        )


class SaveAssistantMessageView(generics.CreateAPIView):
    """POST /api/conversations/<conv_id>/save-message/ — save assistant message after streaming."""

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        conv = get_object_or_404(
            Conversation, id=self.kwargs["conv_id"], user=self.request.user
        )
        serializer.save(conversation=conv, role=Message.Role.ASSISTANT)
