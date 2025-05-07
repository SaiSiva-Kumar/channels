from django.urls import path
from .views import user_channels_view

urlpatterns = [
    path('joined_channels/', user_channels_view),
]