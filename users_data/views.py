from rest_framework.response import Response
from rest_framework.decorators import api_view
from create_channels.models import ChannelInvitation, CreatorChannelData

@api_view(['GET'])
def user_channels_view(request):
    user_uid = getattr(request, 'user_uid', None)

    if not user_uid:
        return Response({"detail": "Unauthorized."}, status=401)

    joined_max_id = request.query_params.get('joined_max_id')
    created_max_id = request.query_params.get('created_max_id')

    joined_channels_qs = ChannelInvitation.objects.filter(user_id=user_uid)
    created_channels_qs = CreatorChannelData.objects.filter(creator_id=user_uid)

    if joined_max_id and not joined_channels_qs.filter(id__gt=joined_max_id).exists():
        joined_channels = None
        total_joined = 0
        latest_joined_id = joined_max_id
    else:
        joined_channels = list(joined_channels_qs.values_list('channel_name', flat=True))
        total_joined = joined_channels_qs.count()
        latest_joined = joined_channels_qs.order_by('-id').first()
        latest_joined_id = latest_joined.id if latest_joined else None

    if created_max_id and not created_channels_qs.filter(channel_id__gt=created_max_id).exists():
        created_channels = None
        total_created = 0
        latest_created_id = created_max_id
    else:
        created_channels = list(created_channels_qs.values_list('channel_name', flat=True))
        total_created = created_channels_qs.count()
        latest_created = created_channels_qs.order_by('-channel_id').first()
        latest_created_id = latest_created.channel_id if latest_created else None

    return Response({
        "joined_channels": {
            "total_channels": total_joined,
            "channels": joined_channels,
            "last_id": latest_joined_id
        },
        "created_channels": {
            "total_channels": total_created,
            "channels": created_channels,
            "last_id": latest_created_id
        }
    })
