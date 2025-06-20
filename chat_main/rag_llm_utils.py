import requests
import json
import logging
from django.conf import settings
from channels.db import database_sync_to_async

logger = logging.getLogger("RAG_Classifier")

@database_sync_to_async
def classify_creator_question(question: str) -> dict:
    prompt = f"""You are a Channel-Creator Assistant. Your sole job is to decide which data-retrieval function to call based on the creator’s question about today’s channel activity (joins, time-outs, bans). Always assume the period is “today.”

Respond with valid JSON only, following this exact schema:
{{
  "tool":     "get_new_users" | "get_timed_out_users" | "get_banned_users" | "none",
  "args":     {{ "period": "today", "names": boolean }},
  "template": string
}}

Rules:
- If the question asks about how many joined, choose "get_new_users".
- If it asks who joined, set "names": true; otherwise false.
- If it asks about time-outs, choose "get_timed_out_users".
- If it asks about bans, choose "get_banned_users".
- If the question is not about joins, time-outs, or bans today, respond exactly: {"tool":"none"}

Now process this question:
\"\"\"{question}\"\"\"
"""
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mistral-nemo:free",
        "max_tokens": 200,
        "temperature": 0.0,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=payload
        )
        if response.status_code != 200:
            logger.error(f"OpenRouter error: {response.status_code} {response.text}")
            return {"tool": "none"}
        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception as e:
        logger.exception("RAG classification failed")
        return {"tool": "none"}
