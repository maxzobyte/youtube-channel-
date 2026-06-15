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
            "temperature": 0.9,
            "maxOutputTokens": max_tokens,
        }
    }

    for attempt in range(1, max_retries + 1):
        resp = requests.post(GEMINI_URL, json=payload, timeout=60)
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = min(60, 5 * (2 ** (attempt - 1)))  # 5, 10, 20, 40, 60s
            print(f"  Gemini returned {resp.status_code}, retrying in {wait}s "
                  f"(attempt {attempt}/{max_retries})...")
            print(f"  Response body: {resp.text[:1000]}")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    # Final attempt: raise the real error if all retries exhausted
    print(f"  Final response body: {resp.text[:1000]}")
    resp.raise_for_status()


def extract_json(text):
    """Extract a JSON object/array from model output, stripping markdown fences."""
    text = text.strip()
    # Remove markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH) as f:
            return json.load(f)
    return {"long": [], "short": []}


def save_history(history):
    # Trim to last MAX_HISTORY_ITEMS entries per list
    history["long"] = history["long"][-MAX_HISTORY_ITEMS:]
    history["short"] = history["short"][-MAX_HISTORY_ITEMS:]
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)


def build_history_block(titles):
    if not titles:
        return ""
    bullet_list = "\n".join(f"- {t}" for t in titles)
    return (
        "\n\nIMPORTANT: You have already covered these topics/titles in previous videos. "
        "Do NOT repeat any of them, and pick a topic that is meaningfully different "
        "(different subtopic, angle, or business concept):\n" + bullet_list + "\n"
    )


LONG_PROMPT_TEMPLATE = """You are a scriptwriter for a faceless YouTube channel about "Business in the 21st Century" \
(topics: startups, business models, AI's impact on work, future of business, entrepreneurship, modern economy, \
remote work, digital marketing, e-commerce, finance trends).

Pick ONE specific, interesting topic within this niche (different each time, be creative — avoid generic \
"what is a startup" type topics, go specific e.g. "Why subscription businesses are taking over" or \
"The rise of solopreneurs powered by AI").
{history_block}
Write a video script for a 6-9 minute narrated explainer video. The script must be broken into 10-16 segments. \
Each segment should be a self-contained chunk of narration (2-4 sentences, conversational, engaging, no fluff), \
plus 2-4 short keywords describing what image should appear on screen during that segment (keywords should be \
simple, concrete, searchable terms like "office team meeting", "stock market chart", "laptop coding", etc — \
think of what a stock photo site would have), plus a short on-screen text overlay (3-8 words, punchy, \
Notion-style key phrase summarizing the segment's main point).

Return ONLY a valid JSON object with this exact structure, no markdown, no commentary:

{{
  "title": "Catchy YouTube title (60-70 chars, include a hook)",
  "description": "YouTube description, 2-3 sentences summarizing the video plus a call to action to subscribe",
  "tags": ["tag1", "tag2", "tag3", "... 10-15 relevant SEO tags"],
  "segments": [
    {{
      "narration": "Text to be spoken for this segment.",
      "image_keywords": ["keyword1", "keyword2"],
      "overlay_text": "Short Punchy Phrase"
    }}
  ]
}}
"""

SHORT_PROMPT_TEMPLATE = """You are a scriptwriter for a faceless YouTube Shorts channel about "Business in the 21st Century".

Write a script for a vertical YouTube Short (45-58 seconds when narrated). It should be a punchy, hook-driven \
piece of content: a surprising fact, a quick tip, or a fast take on a modern business trend. Strong hook in the \
first segment to stop scrolling.
{history_block}
Break it into 5-8 short segments. Each segment: 1-2 sentences of narration (punchy, fast-paced, conversational), \
2-3 image keywords (simple searchable stock photo terms), and a short on-screen text overlay (2-6 words, bold).

Return ONLY a valid JSON object with this exact structure, no markdown, no commentary:

{{
  "title": "Catchy YouTube Shorts title (under 60 chars, include relevant hook/emoji optional)",
  "description": "Short description, 1-2 sentences plus #Shorts hashtag and a call to action to subscribe",
  "tags": ["tag1", "tag2", "... 8-12 relevant SEO tags including 'Shorts'"],
  "segments": [
    {{
      "narration": "Text to be spoken for this segment.",
      "image_keywords": ["keyword1", "keyword2"],
      "overlay_text": "Short Phrase"
    }}
  ]
}}
"""


def main():
    history = load_history()

    print("Generating long-form script...")
    long_prompt = LONG_PROMPT_TEMPLATE.format(history_block=build_history_block(history["long"]))
    long_text = call_gemini(long_prompt, max_tokens=4096)
    long_script = extract_json(long_text)
    with open("script_long.json", "w") as f:
        json.dump(long_script, f, indent=2)
    print(f"Long script: '{long_script['title']}' ({len(long_script['segments'])} segments)")

    print("Generating short-form script...")
    short_prompt = SHORT_PROMPT_TEMPLATE.format(history_block=build_history_block(history["short"]))
    short_text = call_gemini(short_prompt, max_tokens=1536)
    short_script = extract_json(short_text)
    with open("script_short.json", "w") as f:
        json.dump(short_script, f, indent=2)
    print(f"Short script: '{short_script['title']}' ({len(short_script['segments'])} segments)")

    # Update history with the new titles
    history["long"].append(long_script["title"])
    history["short"].append(short_script["title"])
    save_history(history)


if __name__ == "__main__":
    main()
