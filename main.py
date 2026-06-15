"""
Main orchestration script: runs the full daily pipeline for both the long-form video
and the short, end to end:
  1. Generate scripts (Gemini)
  2. Generate narration audio (Edge-TTS)
  3. Fetch background images (Pixabay)
  4. Assemble videos (MoviePy)
  5. Upload to YouTube
"""

import asyncio
import os
import subprocess
import sys

from generate_script import main as generate_scripts
from generate_voice import process_script as generate_voice
from generate_images import process_script as generate_images
from upload_youtube import upload_video


def run_pipeline_for(script_path, audio_dir, image_dir, video_path, orientation, is_short):
    print(f"\n=== Processing {script_path} ({orientation}) ===")

    print("-> Generating voice narration...")
    asyncio.run(generate_voice(script_path, audio_dir))

    print("-> Fetching images...")
    generate_images(script_path, image_dir, orientation)

    print("-> Assembling video...")
    subprocess.run(
        [sys.executable, "make_video.py", script_path, video_path, orientation],
        check=True,
    )

    print("-> Uploading to YouTube...")
    upload_video(video_path, script_path, is_short=is_short, privacy_status="public")


def main():
    print("=== Step 1: Generating scripts ===")
    generate_scripts()

    # Long-form video (horizontal)
    run_pipeline_for(
        script_path="script_long.json",
        audio_dir="audio_long",
        image_dir="images_long",
        video_path="video_long.mp4",
        orientation="horizontal",
        is_short=False,
    )

    # Short video (vertical)
    run_pipeline_for(
        script_path="script_short.json",
        audio_dir="audio_short",
        image_dir="images_short",
        video_path="video_short.mp4",
        orientation="vertical",
        is_short=True,
    )

    print("\n=== All done! ===")


if __name__ == "__main__":
    main()
