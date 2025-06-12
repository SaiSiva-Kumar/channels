from firebase_admin import auth
from urllib.parse import parse_qs
from create_channels.models import ChannelInvitation, CreatorChannelData
from chat_main.models import ChatMessage, UserModeration
from asgiref.sync import sync_to_async

PAGE_SIZE = 20

class FirebaseAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return self.inner(scope)

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        channel_name = query_params.get('channel_name', [None])[0]

        if token is None:
            await send({"type": "websocket.close", "code": 4001})
            return

        try:
            decoded_token = auth.verify_id_token(token)
            user_uid = decoded_token.get("uid")
            user_name = decoded_token.get("name")
            scope['user_uid'] = user_uid
            scope['name'] = user_name
        except Exception:
            await send({"type": "websocket.close", "code": 4003})
            return

        if channel_name is None:
            await send({"type": "websocket.close", "code": 4004})
            return

        try:
            channel = await sync_to_async(CreatorChannelData.objects.get)(channel_name=channel_name)
        except CreatorChannelData.DoesNotExist:
            await send({"type": "websocket.close", "code": 4005})
            return

        is_banned = await sync_to_async(UserModeration.objects.filter(
            user_id=user_uid,
            channel_name=channel_name,
            is_banned=True
        ).exists)()
        if is_banned:
            await send({"type": "websocket.close", "code": 4007})
            return

        path = scope.get("path", "")
        is_rag = path.startswith("/ws/rag/")

        if is_rag:
            if channel.creator_id != user_uid:
                await send({"type": "websocket.close", "code": 4006})
                return
        else:
            if channel.creator_id != user_uid:
                exists = await sync_to_async(ChannelInvitation.objects.filter(
                    user_id=user_uid,
                    channel_name=channel_name
                ).exists)()
                if not exists:
                    await send({"type": "websocket.close", "code": 4006})
                    return

        scope["is_creator"] = (channel.creator_id == user_uid)

        if channel.creator_id == user_uid:
            messages = await sync_to_async(list)(
                ChatMessage.objects.filter(channel=channel_name).order_by("created_at").values("user_id", "message", "created_at")[:PAGE_SIZE]
            )
        else:
            invite = await sync_to_async(ChannelInvitation.objects.get)(user_id=user_uid, channel_name=channel_name)
            messages = await sync_to_async(list)(
                ChatMessage.objects.filter(channel=channel_name, created_at__gte=invite.joined_at).order_by("created_at").values("user_id", "message", "created_at")[:PAGE_SIZE]
            )

        for msg in messages:
            msg["created_at"] = msg["created_at"].isoformat()

        scope["chat_history"] = messages if messages else None
        return await self.inner(scope, receive, send)

def FirebaseAuthMiddlewareStack(inner):
    return FirebaseAuthMiddleware(inner)