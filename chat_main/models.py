from django.db import models

class ChatMessage(models.Model):
    user_id = models.CharField(max_length=255)
    message = models.TextField()
    channel = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages_data"."chat_message'



class UserModeration(models.Model):
    user_id = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255)
    channel_name = models.CharField(max_length=255)
    is_banned = models.BooleanField(default=False)
    banned_reason = models.TextField(blank=True, null=True)
    banned_reason_message = models.TextField(blank=True, null=True)
    banned_at = models.DateTimeField(blank=True, null=True)
    timed_out_reason = models.TextField(blank=True, null=True)
    timed_out_reason_message = models.TextField(blank=True, null=True)
    timed_out_initial_time = models.DateTimeField(blank=True, null=True)
    is_timed_out_duration_completed = models.BooleanField(default=True)

    class Meta:
        db_table = 'user_banned_or_timedout_reason"."user_moderation'