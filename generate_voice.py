"""
Generates narration audio for each segment of a script using Edge-TTS (free, no API key).
Produces individual audio files per segment plus a combined audio file, and records durations.
"""

import asyncio
import json
import os
import sys
import edge_tts
from mutagen.mp3 import MP3

VOICE = "en-US-GuyNeural"  # Natural-sounding free voice. Alternatives: en-US-JennyNeural, en-GB-RyanNeural


async def generate_audio(text, out_path):
    communicate = edge_tts.Communicate(text, VOICE, rate="+5%")
    await communicate.save(out_path)


def get_duration(path):
    audio = MP3(path)
    return audio.info.length


async def process_script(script_path, audio_dir):
    os.makedirs(audio_dir, exist_ok=True)
    with open(script_path) as f:
        script = json.load(f)

    for i, seg in enumerate(script["segments"]):
        out_path = os.path.join(audio_dir, f"seg_{i:03d}.mp3")
        print(f"Generating audio for segment {i}: {seg['narration'][:50]}...")
        await generate_audio(seg["narration"], out_path)
        seg["audio_path"] = out_path
        seg["duration"] = get_duration(out_path)

    with open(script_path, "w") as f:
        json.dump(script, f, indent=2)

    total = sum(s["duration"] for s in script["segments"])
    print(f"Done. Total narration duration: {total:.1f}s")


if __name__ == "__main__":
    script_path = sys.argv[1]
    audio_dir = sys.argv[2]
    asyncio.run(process_script(script_path, audio_dir))
