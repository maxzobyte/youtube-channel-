"""
Assembles a video from a script JSON (with audio_path, image_path, duration, overlay_text per segment).
Applies a Ken Burns zoom effect to images, Notion-style text overlay captions, and concatenates
all segments with their narration audio into a final video.

Usage: python make_video.py <script.json> <output.mp4> <orientation: horizontal|vertical>
"""

import json
import sys
from moviepy import (
    ImageClip,
    ColorClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    concatenate_audioclips,
)

# Resolution presets
RES = {
    "horizontal": (1920, 1080),
    "vertical": (1080, 1920),
}

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def ken_burns_clip(image_path, duration, size, zoom_start=1.0, zoom_end=1.12):
    """Create a clip from a still image with a slow zoom (Ken Burns effect)."""
    clip = ImageClip(image_path)

    # Resize image to cover the target resolution
    w, h = size
    img_w, img_h = clip.size
    scale = max(w / img_w, h / img_h)
    base_size = (int(img_w * scale) + 4, int(img_h * scale) + 4)
    clip = clip.resized(base_size)

    def resize_func(t):
        progress = t / duration if duration > 0 else 0
        zoom = zoom_start + (zoom_end - zoom_start) * progress
        return zoom

    clip = clip.resized(resize_func)
    clip = clip.with_position(("center", "center"))
    clip = clip.with_duration(duration)

    # Crop to exact target size, centered
    bg = ColorClip(size=size, color=(0, 0, 0)).with_duration(duration)
    composite = CompositeVideoClip([bg, clip], size=size)
    return composite


def make_text_overlay(text, size, duration):
    """Create a Notion-style text overlay clip: bold text on a semi-transparent dark bar."""
    w, h = size
    fontsize = int(w * 0.045)

    txt_clip = TextClip(
        font=FONT,
        text=text,
        font_size=fontsize,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="caption",
        size=(int(w * 0.85), None),
        text_align="center",
    )
    txt_clip = txt_clip.with_duration(duration)

    # Semi-transparent dark bar behind the text for readability
    bar_h = txt_clip.h + int(h * 0.04)
    bar = ColorClip(size=(w, bar_h), color=(0, 0, 0)).with_opacity(0.45).with_duration(duration)

    y_pos = int(h * 0.76)
    bar = bar.with_position(("center", y_pos))
    txt_clip = txt_clip.with_position(("center", y_pos + int(h * 0.02)))

    return [bar, txt_clip]


def build_segment_clip(seg, size):
    audio = AudioFileClip(seg["audio_path"])
    duration = audio.duration + 0.3  # small pad at end

    visual = ken_burns_clip(seg["image_path"], duration, size)

    layers = [visual]
    overlay_text = seg.get("overlay_text")
    if overlay_text:
        layers.extend(make_text_overlay(overlay_text, size, duration))

    composite = CompositeVideoClip(layers, size=size).with_duration(duration)
    composite = composite.with_audio(audio)
    return composite


def main():
    script_path = sys.argv[1]
    output_path = sys.argv[2]
    orientation = sys.argv[3] if len(sys.argv) > 3 else "horizontal"

    size = RES[orientation]

    with open(script_path) as f:
        script = json.load(f)

    clips = []
    for i, seg in enumerate(script["segments"]):
        if not seg.get("image_path") or not seg.get("audio_path"):
            print(f"Skipping segment {i}: missing image or audio")
            continue
        print(f"Building segment {i}/{len(script['segments'])}...")
        clips.append(build_segment_clip(seg, size))

    print("Concatenating segments...")
    final = concatenate_videoclips(clips, method="compose")

    print(f"Writing video to {output_path} ...")
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium",
    )
    print("Done.")


if __name__ == "__main__":
    main()
