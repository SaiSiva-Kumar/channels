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
        tool = spec["classification"]["tool"]
        args = spec["classification"]["args"]
        template = spec["template"]

        if tool == "get_new_users":
            result = await get_new_users(self.scope["url_route"]["kwargs"]["channel_name"], args["period"], args["names"])
        elif tool == "get_timed_out_users":
            result = await get_timed_out_users(self.scope["url_route"]["kwargs"]["channel_name"], args["period"], args["names"])
        elif tool == "get_banned_users":
            result = await get_banned_users(self.scope["url_route"]["kwargs"]["channel_name"], args["period"], args["names"])
        else:
            await self.send_json({"type": "response", "text": template})
            return

        if isinstance(result, int):
            try:
                reply = template.format(count=result)
            except (IndexError, KeyError):
                try:
                    reply = template.format(result)
                except Exception:
                    reply = template
        else:
            users_str = ", ".join(result)
            try:
                reply = template.format(users=users_str)
            except (IndexError, KeyError):
                try:
                    reply = template.format(users_str)
                except Exception:
                    reply = template

        await self.send_json({"type": "response", "text": reply})
