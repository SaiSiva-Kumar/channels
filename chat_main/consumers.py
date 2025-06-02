import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from chat_main.models import ChatMessage, UserModeration
from chat_main.llm_utils import check_message_with_llm, get_channel_info, explain_timeout_reason

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        params = parse_qs(query_string)
        self.room_name = params.get('channel_name', [''])[0]
        self.room_group_name = f'chat_{self.room_name}'
        self.user_id = self.scope.get('user_uid')
        channel_key = f"channel:{self.room_name}"
        count_key = f"{channel_key}:count"
        data = cache.get(channel_key)
        if data is None:
            data = await get_channel_info(self.room_name)
            cache.set(channel_key, data, 300)
        cache.set(count_key, cache.get(count_key, 0) + 1)
        self.channel_data = data
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        if self.scope.get("chat_history") is not None:
            await self.send(text_data=json.dumps({"previous_messages": self.scope["chat_history"]}))
        else:
            await self.send(text_data=json.dumps({"previous_messages": None}))

    async def disconnect(self, close_code):
        channel_key = f"channel:{self.room_name}"
        count_key = f"{channel_key}:count"
        count = cache.get(count_key, 0)
        if count > 1:
            cache.set(count_key, count - 1)
            print("channel data is in cache")
        else:
            cache.delete(count_key)
            cache.delete(channel_key)
            print("channel data is not in cache")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        now = timezone.now()
        data = json.loads(text_data)

        if data.get("action") == "load_older":
            before_id = data.get("before")
            older = await self.fetch_older_messages(self.room_name, before_id, 20)
            await self.send(text_data=json.dumps({"older_messages": older}))
            return

        message = data.get("message")
        if message.strip() == "@AI what was my last timed out reason":
            record = await self.get_last_timeout(self.user_id, self.room_name)
            if not record:
                await self.send(text_data=json.dumps({"message": "You have not been timed out recently."}))
                return
            explanation = await explain_timeout_reason(record.timed_out_reason, record.timed_out_reason_message)
            await self.send(text_data=json.dumps({"message": explanation}))
            return

        is_timed_out, remaining_time = await self.is_user_timed_out(self.user_id, self.room_name, now)
        if is_timed_out:
            await self.send(text_data=json.dumps({"message": f"You are timed out for {remaining_time} more seconds."}))
            return

        channel_info = self.channel_data
        llm_response = await check_message_with_llm(message, channel_info)

        if llm_response["status"] == "approved":
            await self.save_message(self.user_id, message, self.room_name)
            name = self.scope.get("name")
            await self.channel_layer.group_send(self.room_group_name, {'type': 'chat_message', 'message': message, 'name': name})
            await self.send(text_data=json.dumps({"message": "Message delivered", "relevance": "Relevant as per channel description"}))

        elif llm_response["status"] == "timeout":
            await self.log_timeout(self.user_id, self.room_name, llm_response.get("reason", ""), message)
            await self.send(text_data=json.dumps({"message": "You have been timed out for violating channel rules."}))

        elif llm_response["status"] == "banned":
            await self.log_ban(self.user_id, self.room_name, llm_response.get("reason", ""), message)
            await self.send(text_data=json.dumps({"message": "You have been banned for violating channel rules."}))
            await self.close()

        else:
            await self.send(text_data=json.dumps({"message": "Your message was removed for being off-topic. Please stay on the channel's subject."}))
            return

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'name': event['name'], 'message': event['message']}))

    @database_sync_to_async
    def save_message(self, user_id, message, channel):
        ChatMessage.objects.create(user_id=user_id, message=message, channel=channel, created_at=timezone.now())

    @database_sync_to_async
    def log_timeout(self, user_id, channel_name, reason, message):
        UserModeration.objects.create(user_id=user_id, user_name=self.scope.get("name"), is_banned=False, channel_name=channel_name, timed_out_reason=reason, timed_out_reason_message=message, timed_out_initial_time=timezone.now(), is_timed_out_duration_completed=False)

    @database_sync_to_async
    def log_ban(self, user_id, channel_name, reason, message):
        UserModeration.objects.create(user_id=user_id, user_name=self.scope.get("name"), is_banned=True, channel_name=channel_name, banned_reason=reason, banned_reason_message=message, banned_at=timezone.now())

    @database_sync_to_async
    def is_user_timed_out(self, user_id, channel_name, now):
        entry = UserModeration.objects.filter(user_id=user_id, channel_name=channel_name).order_by('-timed_out_initial_time').first()
        if entry:
            if entry.is_timed_out_duration_completed:
                return False, 0
            time_diff = now - entry.timed_out_initial_time
            if time_diff < timedelta(minutes=1):
                return True, int((timedelta(minutes=1) - time_diff).total_seconds())
            else:
                entry.is_timed_out_duration_completed = True
                entry.save()
                return False, 0
        return False, 0

    @database_sync_to_async
    def get_last_timeout(self, user_id, channel_name):
        return UserModeration.objects.filter(user_id=user_id, channel_name=channel_name, is_banned=False, timed_out_reason__isnull=False).order_by('-timed_out_initial_time').first()

    @database_sync_to_async
    def fetch_older_messages(self, channel_name, before_id, limit):
        qs = (
            ChatMessage.objects
            .filter(channel=channel_name, id__lt=before_id)
            .order_by('-id')[:limit]
        )
        result = [
            {
                "id": m.id,
                "user_id": m.user_id,
                "message": m.message,
                "created_at": m.created_at.isoformat()
            }
            for m in reversed(qs)
        ]
        return result