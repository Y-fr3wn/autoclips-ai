#!/usr/bin/env python3
"""Exercise FFmpeg's vertical crop, subtitle burn-in and MP4 output without AI downloads."""
from pathlib import Path
import json
import subprocess
import tempfile

def run(args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
         "-i", "testsrc2=size=640x360:rate=15",
         "-f", "lavfi", "-i", "sine=frequency=440",
         "-t", "2", "-c:v", "libx264", "-preset", "ultrafast",
         "-c:a", "aac", str(d/"source.mp4")])
    (d/"clip_01.srt").write_text("1\n00:00:00,000 --> 00:00:01,500\nHello test\n", encoding="utf-8")
    vf = ("crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',"
          "scale=720:1280,setsar=1,"
          "subtitles=clip_01.srt:force_style='FontSize=15,Alignment=2,MarginV=65'")
    run(["ffmpeg", "-v", "error", "-y", "-i", "source.mp4",
         "-t", "1.5", "-vf", vf, "-c:v", "libx264",
         "-preset", "ultrafast", "-c:a", "aac", "clip_01.mp4"], cwd=d)
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "json",
         str(d/"clip_01.mp4")], check=True, capture_output=True, text=True)
    stream = json.loads(result.stdout)["streams"][0]
    assert (stream["width"], stream["height"]) == (720, 1280), stream
    assert (d/"clip_01.mp4").stat().st_size > 0
    print("PASS: vertical 720x1280 MP4 with subtitles")
