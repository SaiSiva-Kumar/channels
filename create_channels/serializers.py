from rest_framework import serializers
from .models import CreatorChannelData, ChannelInvitation

class CreatorChannelDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreatorChannelData
        fields = '__all__'


class ChannelInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelInvitation
        fields = ['id', 'user_id', 'channel_name']