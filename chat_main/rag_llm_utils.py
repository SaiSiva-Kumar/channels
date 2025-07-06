import requests
import json
import logging
import datetime
from django.conf import settings
from channels.db import database_sync_to_async
from create_channels.models import CreatorChannelData

logger = logging.getLogger("RAG_Classifier")

@database_sync_to_async
def classify_creator_query(question: str, channel_name: str) -> dict:
    try:
        created = CreatorChannelData.objects.get(channel_name=channel_name).created_at.date()
        first_date = created.strftime("%d/%m/%Y")
    except CreatorChannelData.DoesNotExist:
        first_date = datetime.date.today().strftime("%d/%m/%Y")
    today = datetime.date.today().strftime("%d/%m/%Y")
    prompt = f"""You are a Channel-Creator Assistant whose job is to interpret a creator’s question about how many users joined, were timed-out, or were banned on a specific date—and to generate a JSON with keys "tool", "args", and "template". The "date" in args must be in DD/MM/YYYY format, and must not be earlier than {first_date} or later than {today}. Use varied natural phrasing in the template, including placeholder {{count}} or {{users}}. Always output valid JSON only, with this schema:

{{
  "tool":      "get_new_users" | "get_timed_out_users" | "get_banned_users" | "none",
  "args":      {{ "date": "DD/MM/YYYY", "names": boolean }},
  "template":  string
}}

Now process the question below exactly:
\"\"\"{question}\"\"\"
"""
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mistral-nemo:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 250,
        "temperature": 0.2
    }
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        if r.status_code != 200:
            return {
                "tool": "none",
                "args": {"date": today, "names": False},
                "template": "Sorry—I can only answer counts or names of joins, time-outs, or bans for a given date."
            }
        raw = r.json()["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception:
        logger.exception("RAG classification failed")
        return {
            "tool": "none",
            "args": {"date": today, "names": False},
            "template": "Sorry—I can only answer counts or names of joins, time-outs, or bans for a given date."
        }