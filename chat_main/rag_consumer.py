from channels.generic.websocket import AsyncJsonWebsocketConsumer
from chat_main.rag_llm_utils import classify_creator_query

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
        result = await classify_creator_query(question)
        await self.send_json({
            "type": "response",
            "text": result["reply"]
        })
