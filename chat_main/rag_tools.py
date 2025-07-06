import datetime
from channels.db import database_sync_to_async
from create_channels.models import CreatorChannelData, ChannelInvitation
from chat_main.models import UserModeration

def _parse_date(date_str: str, channel_name: str) -> datetime.date:
    try:
        dt = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
    except:
        dt = datetime.date.today()
    try:
        created = CreatorChannelData.objects.get(channel_name=channel_name).created_at.date()
    except CreatorChannelData.DoesNotExist:
        created = dt
    return max(created, min(dt, datetime.date.today()))

@database_sync_to_async
def get_new_users(channel_name: str, date: str, names: bool):
    dt = _parse_date(date, channel_name)
    qs = ChannelInvitation.objects.filter(channel_name=channel_name, joined_at__date=dt)
    return list(qs.values_list("user_id", flat=True)) if names else qs.count()

@database_sync_to_async
def get_timed_out_users(channel_name: str, date: str, names: bool):
    dt = _parse_date(date, channel_name)
    qs = UserModeration.objects.filter(channel_name=channel_name, timed_out_initial_time__date=dt)
    return list(qs.values_list("user_id", flat=True).distinct()) if names else qs.count()

@database_sync_to_async
def get_banned_users(channel_name: str, date: str, names: bool):
    dt = _parse_date(date, channel_name)
    qs = UserModeration.objects.filter(channel_name=channel_name, is_banned=True, banned_at__date=dt)
    return list(qs.values_list("user_id", flat=True).distinct()) if names else qs.count()