from django.urls import path
from .views import CreatorChannelDataView, JoinChannelView

urlpatterns = [
    path('create-channel/', CreatorChannelDataView.as_view()),
    path('join/', JoinChannelView.as_view()),
]