import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

class GeminiChatCompletionView(APIView):
    def post(self, request):
        user_text = request.data.get("text")
        image_url = request.data.get("image_url")

        if not user_text:
            return Response({"error": "Text message is required."}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        message_content = [{"type": "text", "text": user_text}]
        if image_url:
            message_content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        payload = {
            "model": "mistralai/mistral-small-3.1-24b-instruct:free",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": message_content
                }
            ]
        }

        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            data = response.json()
            if "choices" in data and data["choices"]:
                reply = data["choices"][0]["message"]["content"].replace('\n', ' ').strip()
                return Response({"reply": reply}, status=status.HTTP_200_OK)
            elif "error" in data:
                return Response({"error": data["error"].get("message", "Unknown error")}, status=status.HTTP_502_BAD_GATEWAY)
            else:
                return Response({"error": "Unexpected response format."}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)