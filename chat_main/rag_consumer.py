from channels.generic.websocket import AsyncJsonWebsocketConsumer
from chat_main.rag_llm_utils import classify_creator_query
from chat_main.rag_tools import get_new_users, get_timed_out_users, get_banned_users

class CreatorRagConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if not self.scope.get("is_creator", False):
            return await self.close(code=4006)
        await self.accept()
        await self.send_json({
            "type": "welcome",
            "text": f"👋 Hi {self.scope['name']}, I’m your channel assistant. Ask me about joins, time-outs, or bans."
        })

    async def receive_json(self, content, **kwargs):
        question = content.get("text", "").strip()
        spec = await classify_creator_query(question)
        tool     = spec.get("tool")
        args     = spec.get("args", {})
        template = spec.get("template", "")
        channel  = self.scope["url_route"]["kwargs"]["channel_name"]

        if tool == "get_new_users":
            data = await get_new_users(channel, args.get("date"), args.get("names", False))
        elif tool == "get_timed_out_users":
            data = await get_timed_out_users(channel, args.get("date"), args.get("names", False))
        elif tool == "get_banned_users":
            data = await get_banned_users(channel, args.get("date"), args.get("names", False))
        else:
            return await self.send_json({"type": "response", "text": template})

        if isinstance(data, list):
            users = ", ".join(data)
            count = len(data)
        else:
            count = data
            users = None

        try:
            if users is not None:
                reply = template.format(count=count, users=users)
            else:
                reply = template.format(count=count)
        except Exception:
            try:
                if users is not None:
                    reply = template.format(count, users)
                else:
                    reply = template.format(count)
            except Exception:
                reply = template

        await self.send_json({"type": "response", "text": reply})