"""
Uploads a video to YouTube using the YouTube Data API v3, with title, description, tags,
category, and privacy status pulled from a script JSON file.

Usage: python upload_youtube.py <video.mp4> <script.json> <is_short: true|false>
"""

import json
import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_ID = os.environ["YT_CLIENT_ID"]
CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service():
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds)


def upload_video(video_path, script_path, is_short=False, privacy_status="public"):
    with open(script_path) as f:
        script = json.load(f)

    title = script["title"]
    description = script["description"]
    tags = script.get("tags", [])

    if is_short and "#shorts" not in description.lower() and "#Shorts" not in tags:
        description += "\n\n#Shorts"

    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": "27",  # Education category - good fit for business explainer content
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    print(f"Uploading '{title}'...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Upload complete! Video ID: {video_id}")
    print(f"URL: https://www.youtube.com/watch?v={video_id}")
    return video_id


if __name__ == "__main__":
    video_path = sys.argv[1]
    script_path = sys.argv[2]
    is_short = len(sys.argv) > 3 and sys.argv[3].lower() == "true"
    upload_video(video_path, script_path, is_short=is_short)
