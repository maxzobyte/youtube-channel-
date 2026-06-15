"""
Generates daily video scripts about 21st century business topics using Gemini API.
Produces two scripts: a long-form (5-10 min) and a short-form (<60s).
Output: script_long.json and script_short.json with structured scenes for video assembly.

Keeps a history of past topics/titles in topic_history.json so future runs avoid
repeating the same topics.
"""

import os
import json
import re
import time
import requests

# Retrieve Gemini API credentials from environment variables
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
# Using gemini-1.5-flash for stable and generous free-tier rate limits
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

HISTORY_PATH = "topic_history.json"
MAX_HISTORY_ITEMS = 60  # Keep the last N titles to avoid an ever-growing prompt


def call_gemini(prompt, max_tokens=2048, max_retries=5):
    """Call Gemini API with a text prompt and return the text response.

    Retries with exponential backoff on 429 (rate limit) and 5xx errors,
    since these are common and usually transient on the free tier.
    """
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": max_tokens,
        }
    }

    for attempt in range(1, max_retries + 1):
        resp = requests.post(GEMINI_URL, json=payload, timeout=60)
        
        if resp.status_code == 429 or resp.status_code >= 500:
            # 10s base exponential delay to give the API rate limits time to reset
            wait = min(60, 10 * (2 ** (attempt - 1)))  # 10, 20, 40, 60s
            print(f"  Gemini returned {resp.status_code}, retrying in {wait}s "
                  f"(attempt {attempt}/{max_retries})...")
            time.sleep(wait)
            continue
            
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    # Final attempt: raise the real error if all retries are exhausted
    print(f"  Final response body: {resp.text[:1000]}")
    resp.raise_for_status()


def extract_json(text):
    """Extract a JSON object/array from model output, stripping markdown fences."""
    text = text.strip()
    # Remove markdown code fences if present (e.g. ```json ... ```)
    text = re.sub(r"^
