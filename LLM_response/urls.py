from django.urls import path
from .views import GeminiChatCompletionView

urlpatterns = [
    path("api/chat/", GeminiChatCompletionView.as_view(), name="gemini-chat"),
]