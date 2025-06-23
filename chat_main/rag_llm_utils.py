import requests
import json
import logging
from django.conf import settings
from channels.db import database_sync_to_async

logger = logging.getLogger("RAG_Classifier")

@database_sync_to_async
def classify_creator_query(question: str) -> dict:
    prompt = f"""You are a Channel-Creator Assistant. Your only job is to interpret a creator’s question about today’s channel activity (joins, time-outs, bans) and output a single JSON object with two keys:

{{
  "classification": {{
    "tool":   "get_new_users" | "get_timed_out_users" | "get_banned_users" | "none",
    "args":   {{ "period": "today", "names": boolean }}
  }},
  "reply":  string
}}

– `"classification"` tells our system which query to run and with what arguments.  
– `"reply"` is a fixed, human-friendly acknowledgment sentence (no counts or lists).

Rules:
1. If the question asks how many users joined today, set `"tool": "get_new_users"`.
2. If it asks who joined (or “names”), set `"names": true`; otherwise `false`.
3. If it asks about time-outs today, set `"tool": "get_timed_out_users"`.
4. If it asks about bans today, set `"tool": "get_banned_users"`.
5. Always set `"period": "today"`.
6. If the question is out of scope, set `"tool": "none"` and `"reply": "Sorry—I can only talk about today’s joins, time-outs, or bans."`

Now process this question:
\"\"\"{question}\"\"\"
"""
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mistral-nemo:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.0
    }
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=payload
        )
        if r.status_code != 200:
            logger.error(f"OpenRouter error: {r.status_code} {r.text}")
            return {
                "classification": {"tool": "none", "args": {"period": "today", "names": False}},
                "reply": "Sorry—I can only talk about today’s joins, time-outs, or bans."
            }
        raw = r.json()["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception:
        logger.exception("RAG classification failed")
        return {
            "classification": {"tool": "none", "args": {"period": "today", "names": False}},
            "reply": "Sorry—I can only talk about today’s joins, time-outs, or bans."
        }
