import requests
import json
import logging
import datetime
from django.conf import settings
from channels.db import database_sync_to_async

logger = logging.getLogger("RAG_Classifier")

@database_sync_to_async
def classify_creator_query(question: str) -> dict:
    prompt = f"""You are a Channel-Creator Assistant. Your sole job is to interpret a creator’s question about how many users joined, were timed-out, or were banned on a specific date—and optionally provide their names.

Always output valid JSON only, following this exact schema:
{{
  "tool":      "get_new_users" | "get_timed_out_users" | "get_banned_users" | "none",
  "args":      {{
     "date": "<YYYY-MM-DD>",
     "names": boolean
  }},
  "template":  string
}}

Rules:
1. If the question says "yesterday", set "date" to yesterday’s date.
2. If the question contains an explicit YYYY-MM-DD, use that date.
3. Otherwise default "date" to today’s date.
4. If the question asks for names, set "names" to true; otherwise false.
5. If asking about joins, set "tool" to "get_new_users".
6. If asking about time-outs, set "tool" to "get_timed_out_users".
7. If asking about bans, set "tool" to "get_banned_users".
8. If out of scope, set "tool" to "none" and "template" to "Sorry—I can only answer counts or names of joins, time-outs, or bans for a given date."

Now process this question and return the JSON:
\"\"\"{question}\"\"\"
"""
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mistral-nemo:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.0
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        if response.status_code != 200:
            return {
                "tool": "none",
                "args": {"date": datetime.date.today().isoformat(), "names": False},
                "template": "Sorry—I can only answer counts or names of joins, time-outs, or bans for a given date."
            }
        raw = response.json()["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception:
        logger.exception("RAG classification failed")
        return {
            "tool": "none",
            "args": {"date": datetime.date.today().isoformat(), "names": False},
            "template": "Sorry—I can only answer counts or names of joins, time-outs, or bans for a given date."
        }
