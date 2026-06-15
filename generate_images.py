"""
Fetches a relevant background image for each segment of a script using the Pixabay API (free).
Downloads images into an output directory and records the local path in the script JSON.
"""

import json
import os
import sys
import time
import requests

PIXABAY_API_KEY = os.environ["PIXABAY_API_KEY"]
PIXABAY_URL = "https://pixabay.com/api/"

# Track used image IDs across segments to avoid repeats within a single video
USED_IDS = set()


def search_image(keywords, orientation="horizontal"):
    """Search Pixabay for an image matching the given keywords. Returns the largeImageURL or None."""
    query = " ".join(keywords)
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "image_type": "photo",
        "orientation": orientation,
        "safesearch": "true",
        "per_page": 20,
        "order": "popular",
        "min_width": 1280 if orientation == "horizontal" else 720,
    }
    resp = requests.get(PIXABAY_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    hits = data.get("hits", [])

    # Prefer an unused image
    for hit in hits:
        if hit["id"] not in USED_IDS:
            USED_IDS.add(hit["id"])
            return hit["largeImageURL"]

    # Fall back to first result even if reused, or None if no results
    if hits:
        return hits[0]["largeImageURL"]
    return None


def download_image(url, out_path):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)


def process_script(script_path, image_dir, orientation="horizontal"):
    os.makedirs(image_dir, exist_ok=True)
    with open(script_path) as f:
        script = json.load(f)

    for i, seg in enumerate(script["segments"]):
        keywords = seg.get("image_keywords", ["business"])
        print(f"Segment {i}: searching for {keywords}")

        url = search_image(keywords, orientation=orientation)
        if url is None:
            # Fallback to a generic business search
            print(f"  No results, falling back to generic 'business' search")
            url = search_image(["business", "office"], orientation=orientation)

        out_path = os.path.join(image_dir, f"seg_{i:03d}.jpg")
        if url:
            download_image(url, out_path)
            seg["image_path"] = out_path
            print(f"  Saved -> {out_path}")
        else:
            seg["image_path"] = None
            print(f"  WARNING: no image found for segment {i}")

        time.sleep(0.5)  # be gentle with the API

    with open(script_path, "w") as f:
        json.dump(script, f, indent=2)


if __name__ == "__main__":
    script_path = sys.argv[1]
    image_dir = sys.argv[2]
    orientation = sys.argv[3] if len(sys.argv) > 3 else "horizontal"
    process_script(script_path, image_dir, orientation)
