# Daily Business YouTube Automation

Fully automated pipeline that generates and uploads one long-form video and one Short
to YouTube every day, on the topic of "Business in the 21st Century".

## Pipeline

1. **Script generation** — Google Gemini API writes a unique script each day, broken
   into segments with narration text, image search keywords, and on-screen text overlays.
2. **Voice narration** — Microsoft Edge TTS (free, no API key) converts each segment's
   narration to speech.
3. **Images** — Pixabay API fetches a relevant royalty-free photo for each segment.
4. **Video assembly** — MoviePy combines images (with a slow Ken Burns zoom), narration
   audio, and Notion-style text overlay captions into a finished MP4.
5. **Upload** — YouTube Data API uploads the video with title, description, and tags
   generated from the script.

## Required GitHub Secrets

Set these under **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key |
| `PIXABAY_API_KEY` | Pixabay API key |
| `YT_CLIENT_ID` | Google Cloud OAuth client ID |
| `YT_CLIENT_SECRET` | Google Cloud OAuth client secret |
| `YT_REFRESH_TOKEN` | OAuth refresh token (generated once via the auth flow) |

## Schedule

The workflow in `.github/workflows/daily-video.yml` runs daily at 08:00 UTC. It can
also be triggered manually from the **Actions** tab using "Run workflow".

## Running locally

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...
export PIXABAY_API_KEY=...
export YT_CLIENT_ID=...
export YT_CLIENT_SECRET=...
export YT_REFRESH_TOKEN=...
python main.py
```

## Avoiding repeated topics

Each run saves the day's video titles to `topic_history.json` in the repo (auto-committed
by the workflow). On the next run, the script prompt includes the list of past titles
and instructs Gemini not to repeat them. The history keeps the last 60 titles per
video type.

## Notes

- Videos are uploaded as **public** by default. Change `privacy_status` in `main.py`
  to `"private"` or `"unlisted"` if you want to review before publishing.
- The OAuth consent screen is in "Testing" mode by default, which limits the refresh
  token's validity to 7 days unless you publish the app (Google Cloud Console →
  OAuth consent screen → Publish App). Publishing as "External" doesn't require
  Google's verification process for personal use with this scope.
