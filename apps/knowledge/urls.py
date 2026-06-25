from django.urls import path
from . import views

urlpatterns = [
    # Knowledge Bases
    path(
        "knowledge-bases/",
        views.KBListCreateView.as_view(),
        name="kb-list-create",
    ),
    path(
        "knowledge-bases/<uuid:pk>/",
        views.KBRetrieveUpdateDestroyView.as_view(),
        name="kb-detail",
    ),
    # Documents
    path(
        "knowledge-bases/<uuid:kb_id>/documents/",
        views.DocumentListCreateView.as_view(),
        name="doc-list-create",
    ),
    path(
        "documents/<uuid:pk>/",
        views.DocumentDestroyView.as_view(),
        name="doc-delete",
    ),
    # Conversations
    path(
        "knowledge-bases/<uuid:kb_id>/conversations/",
        views.ConversationListCreateView.as_view(),
        name="conv-list-create",
    ),
    path(
        "conversations/<uuid:pk>/",
        views.ConversationDetailView.as_view(),
        name="conv-detail",
    ),
    # Chat
    path(
        "knowledge-bases/<uuid:kb_id>/chat/",
        views.ChatView.as_view(),
        name="chat-new",
    ),
    path(
        "conversations/<uuid:conv_id>/chat/",
        views.ContinueChatView.as_view(),
        name="chat-continue",
    ),
    path(
        "conversations/<uuid:conv_id>/messages/",
        views.MessagesListView.as_view(),
        name="conv-messages",
    ),
    path(
        "conversations/<uuid:conv_id>/save-message/",
        views.SaveAssistantMessageView.as_view(),
        name="conv-save-message",
    ),
]
