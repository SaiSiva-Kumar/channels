from channels.generic.websocket import AsyncJsonWebsocketConsumer

class CreatorRagConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if not self.scope.get("is_creator", False):
            return await self.close(code=4006)
        await self.accept()
        await self.send_json({"type": "welcome", "text": f"👋 Hi {self.scope['name']}, I’m your channel assistant. Ask me about joins, time-outs, or bans."})

    async def receive_json(self, content, **kwargs):
        pass