#!/usr/bin/env python3
"""AutoClips AI: initial Arabic/English podcast clipping engine."""
import argparse
import json
import re
import subprocess
from pathlib import Path

HOOKS = ("why", "how", "secret", "mistake", "never", "important", "because",
         "ليه", "إزاي", "ازاي", "سر", "غلط", "مهم", "عشان", "لكن", "تخيل")

def run(command):
    subprocess.run(command, check=True)

def score(words):
    text = " ".join(w["word"] for w in words).strip().lower()
    if not text:
        return -100
    hits = sum(text.count(h) for h in HOOKS)
    return hits * 2 + min(len(text) / 130, 4) + (2 if "؟" in text or "?" in text else 0)

def candidates(segments, min_sec=20, max_sec=65):
    """Generate sentence-aligned windows, with word-timing boundaries when available."""
    words = []
    for seg in segments:
        for w in seg.words or []:
            if w.start is not None and w.end is not None:
                words.append({"start": float(w.start), "end": float(w.end), "word": w.word})
    if not words:
        # fallback for models lacking word alignment
        words = [{"start": float(s.start), "end": float(s.end), "word": s.text} for s in segments]
    if not words:
        return []
    stops = {i for i,w in enumerate(words) if re.search(r"[.!?؟。]\s*$", w["word"])}
    starts = [0] + [i+1 for i in stops if i+1 < len(words)]
    starts = sorted(set(starts))
    results = []
    for i in starts:
        for j in range(i, len(words)):
            duration = words[j]["end"] - words[i]["start"]
            if duration > max_sec:
                break
            if duration < min_sec:
                continue
            if j not in stops and j != len(words)-1:
                continue
            part = words[i:j+1]
            results.append({"start": part[0]["start"], "end": part[-1]["end"],
                            "score": score(part), "words": part})
    return sorted(results, key=lambda c: c["score"], reverse=True)

def choose(items, count):
    chosen = []
    for c in items:
        if all(min(c["end"], x["end"]) - max(c["start"], x["start"]) <= 0 for x in chosen):
            chosen.append(c)
        if len(chosen) >= count:
            break
    return sorted(chosen, key=lambda c: c["start"])

def srt_timestamp(seconds):
    ms = max(0, round(seconds*1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def write_srt(words, clip_start, destination):
    chunks = []
    current = []
    for w in words:
        current.append(w)
        if len(current) >= 5 or re.search(r"[.!?؟]\s*$", w["word"]):
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    with open(destination, "w", encoding="utf-8") as f:
        for n, group in enumerate(chunks, 1):
            start = srt_timestamp(group[0]["start"] - clip_start)
            end = srt_timestamp(group[-1]["end"] - clip_start)
            text = " ".join(w["word"].strip() for w in group).strip()
            f.write(f"{n}\n{start} --> {end}\n{text}\n\n")

def main():
    p = argparse.ArgumentParser(description="Clip Arabic/English podcasts into short videos.")
    p.add_argument("video", help="Local MP4/MOV video file")
    p.add_argument("--output", default="clips")
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--min-seconds", type=int, default=20)
    p.add_argument("--max-seconds", type=int, default=65)
    p.add_argument("--model", default="tiny", help="Whisper model; tiny runs fastest on CPU")
    p.add_argument("--subtitles", action="store_true", help="Burn Arabic/English subtitles")
    args = p.parse_args()
    if not Path(args.video).is_file():
        p.error("Video file not found")
    if args.count < 1 or args.min_seconds < 1 or args.max_seconds <= args.min_seconds:
        p.error("Invalid clip settings")
    from faster_whisper import WhisperModel
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(args.video, word_timestamps=True, vad_filter=True,
                                           beam_size=3)
    segments = list(segments_iter)
    clips = choose(candidates(segments, args.min_seconds, args.max_seconds), args.count)
    if not clips:
        print("No complete speech clips matched the requested duration.")
        return
    metadata = []
    for n, clip in enumerate(clips, 1):
        name = f"clip_{n:02}.mp4"
        duration = clip["end"] - clip["start"]
        # ffmpeg first crops to 9:16 using a centered crop, then scales to 720x1280.
        vf = "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=720:1280,setsar=1"
        if args.subtitles:
            subtitle_path = output / f"clip_{n:02}.srt"
            write_srt(clip["words"], clip["start"], subtitle_path)
            # Use a relative filename while executing from output dir to avoid filter path escaping.
            vf += f",subtitles={subtitle_path.name}:force_style='FontSize=15,Alignment=2,MarginV=65'"
        command = ["ffmpeg", "-y", "-ss", str(clip["start"]), "-i", str(Path(args.video).resolve()),
                   "-t", str(duration), "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
                   "-crf", "24", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", name]
        subprocess.run(command, cwd=output, check=True)
        metadata.append({"file": name, "start": clip["start"], "end": clip["end"],
                         "score": round(clip["score"], 2), "language": info.language})
    (output/"clips.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
