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

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

HISTORY_PATH = "topic_history.json"
MAX_HISTORY_ITEMS = 60  # keep the last N titles to avoid an ever-growing prompt


def call_gemini(prompt, max_tokens=2048, max_retries=5):
    """Call Gemini API with a text prompt and return the text response.

    Retries with exponential backoff on 429 (rate limit) and 5xx errors,
    since these are common and usually transient on the free tier.
    """
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
