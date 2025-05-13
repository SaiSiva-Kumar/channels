import requests
import json
from django.conf import settings
from channels.db import database_sync_to_async
from create_channels.models import CreatorChannelData


@database_sync_to_async
def get_channel_info(channel_name):
    try:
        channel = CreatorChannelData.objects.get(channel_name=channel_name)
        result = {
            "description": channel.channel_description or "",
            "ban_reason": channel.ban_reason if channel.ban_reason else [],
            "timeout_reason": channel.time_out_reason if channel.time_out_reason else []
        }
        print("DB_RESPONSE:", result)
        return result
    except CreatorChannelData.DoesNotExist:
        result = {
            "description": "",
            "ban_reason": [],
            "timeout_reason": []
        }
        print("DB_RESPONSE:", result)
        return result


@database_sync_to_async
def check_message_with_llm(message, channel_data):
    prompt = f"""You are a content moderator analyzing messages in three dimensions. You must carefully analyze each of these dimensions separately.

Channel Description:
"{channel_data['description']}"

Timeout Reasons:
"{channel_data['timeout_reason']}"

Ban Reasons:
"{channel_data['ban_reason']}"

USER MESSAGE:
"{message}"

INSTRUCTIONS:
Analyze the message in these three separate dimensions:

1. DIMENSION ONE - CHANNEL ALIGNMENT:
- Does the message align with or relate to the channel description?
- Messages should be relevant to the channel's theme and purpose.
- If a message is about "breaking bad" and the channel is about "space and astronomy", these topics are unrelated and the message does not align.
- A message must contain content specifically related to the channel's topic to be considered aligned.

2. DIMENSION TWO - TIMEOUT RULES:
- Does the message match any of the timeout reasons?
- Be specific and strict when matching against the timeout reasons listed.
- For example, if "offensive language" is a timeout reason, words like "fuck" should trigger a timeout.

3. DIMENSION THREE - BAN RULES:
- Does the message match any of the ban reasons?
- Be specific and strict when matching against the ban reasons listed.
- Ban violations are the most serious and should be checked carefully.

DECISION MAKING:
- If the message violates any ban reason, return: {{"status": "banned", "reason": "Explain exactly which ban rule was violated, and give a natural, human-like explanation pointing out the specific words or behavior that triggered this."}}
- If the message does not violate ban reasons but violates any timeout reason, return: {{"status": "timeout", "reason": "Explain exactly which timeout rule was violated, and give a natural, human-like explanation pointing out the specific words or behavior that triggered this."}}
- Only if the message aligns with the channel description AND doesn't violate any rules, return: {{"status": "approved"}}

IMPORTANT: You must analyze each dimension thoroughly. A message must satisfy all three dimensions to be approved. Only reply in raw JSON format. Do not add explanations."""

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "mistralai/mistral-nemo:free",
        "max_tokens": 100,
        "temperature": 0.1,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        if response.status_code != 200:
            return {"status": "approved"}
        data = response.json()
        reply_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print("LLM_RESPONSE:", reply_text)
        return json_safe(reply_text)
    except:
        return {"status": "approved"}


def json_safe(text):
    try:
        return json.loads(text)
    except:
        return {"status": "approved"}


@database_sync_to_async
def explain_timeout_reason(message, timeout_reasons):
    print(message, timeout_reasons)
    prompt = f"""You are a content moderation assistant. A user sent the following message:

"{message}"

The channel has these timeout reasons:
{timeout_reasons}

Analyze the message strictly against these timeout reasons and explain in natural, human-like language **why** the message might trigger a timeout. Be clear and specific. Mention the exact words or phrasing that caused it. If no match is found, just say: "No timeout rule was violated."

Only reply with the explanation string, no JSON, no formatting."""

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "mistralai/mistral-nemo:free",
        "max_tokens": 100,
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        if response.status_code != 200:
            return "No timeout rule was violated."
        data = response.json()
        reply_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        reply_text = reply_text.strip()
        reply_text = reply_text.replace('\\"', '"')

        return reply_text
    except:
        return "No timeout rule was violated."
