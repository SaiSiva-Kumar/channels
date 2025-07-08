from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from .models import CreatorChannelData
from .serializers import CreatorChannelDataSerializer, ChannelInvitationSerializer

class CreatorChannelDataView(APIView):
    def post(self, request):
        data = request.data.copy()
        data['creator_id'] = request.user_uid
        serializer = CreatorChannelDataSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "created"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JoinChannelView(APIView):
    serializer_class = ChannelInvitationSerializer

    def post(self, request):
        user_id = getattr(request, 'user_uid', None)
        channel_name = request.query_params.get('channel_name')

        if not channel_name:
            return Response({"channel_name": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            channel = CreatorChannelData.objects.get(channel_name=channel_name)
        except CreatorChannelData.DoesNotExist:
            return Response({"is_channel_exist": False}, status=status.HTTP_404_NOT_FOUND)

        if user_id == channel.creator_id:
            return Response({"creator": True}, status=status.HTTP_200_OK)

        serializer = self.serializer_class(data={"user_id": user_id, "channel_name": channel_name})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({"Joined": True}, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({"is_user_exist": True}, status=status.HTTP_409_CONFLICT)

        if 'non_field_errors' in serializer.errors:
            return Response({"is_user_exist": True}, status=status.HTTP_409_CONFLICT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)