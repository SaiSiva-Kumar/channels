import requests
import json
import logging
from django.conf import settings
from channels.db import database_sync_to_async

logger = logging.getLogger("RAG_Classifier")

@database_sync_to_async
def classify_and_reply(question: str) -> dict:
    prompt = f"""You are a Channel-Creator Assistant. Your only job is to interpret a creator’s question about today’s channel activity (joins, time-outs, bans) and produce two outputs in a single JSON object:

{{
  "classification": {{
    "tool":   "get_new_users" | "get_timed_out_users" | "get_banned_users" | "none",
    "args":   {{ "period": "today", "names": boolean }}
  }},
  "reply": string
}}

Reply must **not** include any counts or user lists—just a natural-language acknowledgement of which data you will fetch.  
Examples of valid replies:
- "Sure—I'll check how many users joined today."
- "Okay, retrieving the list of users timed out today."
- "Got it—fetching today’s banned users."
- For out-of-scope: {"tool":"none","reply":"Sorry—I can only talk about today’s joins, time-outs, or bans."}

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
            return {
                "classification": {"tool": "none", "args": {"period": "today", "names": False}},
                "reply": "Sorry—I can only talk about today’s joins, time-outs, or bans."
            }
        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception:
        logger.exception("RAG classification and reply failed")
        return {
            "classification": {"tool": "none", "args": {"period": "today", "names": False}},
            "reply": "Sorry—I can only talk about today’s joins, time-outs, or bans."
        }
