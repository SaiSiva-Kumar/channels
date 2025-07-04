import datetime
from channels.db import database_sync_to_async
from create_channels.models import ChannelInvitation
from chat_main.models import UserModeration

@database_sync_to_async
def get_new_users(channel_name: str, date: str, names: bool):
    dt = datetime.date.fromisoformat(date)
    qs = ChannelInvitation.objects.filter(
        channel_name=channel_name,
        joined_at__date=dt
    )
    if names:
        return list(qs.values_list("user_id", flat=True))
    return qs.count()

@database_sync_to_async
def get_timed_out_users(channel_name: str, date: str, names: bool):
    dt = datetime.date.fromisoformat(date)
    qs = UserModeration.objects.filter(
        channel_name=channel_name,
        timed_out_initial_time__date=dt
    )
    if names:
        return list(qs.values_list("user_id", flat=True).distinct())
    return qs.count()

@database_sync_to_async
def get_banned_users(channel_name: str, date: str, names: bool):
    dt = datetime.date.fromisoformat(date)
    qs = UserModeration.objects.filter(
        channel_name=channel_name,
        is_banned=True,
        banned_at__date=dt
    )
    if names:
        return list(qs.values_list("user_id", flat=True).distinct())
    return qs.count()
