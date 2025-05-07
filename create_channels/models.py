from django.db import models

class CreatorChannelData(models.Model):
    channel_id = models.AutoField(primary_key=True)
    creator_id = models.CharField(max_length=255)
    channel_name = models.CharField(max_length=255, unique=True, default='temp_channel')
    channel_description = models.TextField()
    ban_reason = models.JSONField()
    time_out_reason = models.JSONField()

    class Meta:
        db_table = 'creators_data"."creator_channel_data'


class ChannelInvitation(models.Model):
    user_id = models.CharField(max_length=255)
    channel_name = models.CharField(max_length=255)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_id', 'channel_name')
        db_table = 'creators_data"."channel_invitation'