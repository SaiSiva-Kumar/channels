# chat_main/rag_llm_utils.py

import requests
import json
import logging
from django.conf import settings
from channels.db import database_sync_to_async

logger = logging.getLogger("RAG_Classifier")

@database_sync_to_async
def classify_creator_query(question: str) -> dict:
    prompt = f"""You are a Channel-Creator Assistant. Your only job is to interpret a creator’s question about today’s channel activity (joins, time-outs, bans) and output valid JSON with two keys:

{{
  "classification": {{
    "tool": "get_new_users" | "get_timed_out_users" | "get_banned_users" | "none",
    "args": {{ "period": "today", "names": boolean }}
  }},
  "template": string
}}

- "tool" indicates which count to fetch.
- "period" must be "today".
- "names" is true if the question asks "who" or "names".
- "template" is a Python .format() template using {{count}} or {{users}}.
- If out of scope, set "tool":"none" and "template":"Sorry—I can only talk about today’s joins, time-outs, or bans."

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
        "max_tokens": 200,
        "temperature": 0.0
    }
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=payload
        )
        if response.status_code != 200:
            logger.error(f"{response.status_code} {response.text}")
            return {
                "classification": {"tool": "none", "args": {"period": "today", "names": False}},
                "template": "Sorry—I can only talk about today’s joins, time-outs, or bans."
            }
        raw = response.json()["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception:
        logger.exception("RAG classification failed")
        return {
            "classification": {"tool": "none", "args": {"period": "today", "names": False}},
            "template": "Sorry—I can only talk about today’s joins, time-outs, or bans."
        }
