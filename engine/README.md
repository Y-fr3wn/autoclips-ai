# AutoClips AI — processing engine (prototype)

This is a real command-line prototype, not yet connected to the website.

## Requirements
Python 3.10+, FFmpeg with libass subtitle filter, and enough CPU/RAM for Whisper.

## Run
```bash
cd engine
python -m pip install -r requirements.txt
python clipper.py /path/to/podcast.mp4 --count 3 --model tiny --subtitles
```

Output: clips/clip_01.mp4 etc, optional SRT files, and clips.json.

Arabic and English speech are auto-detected by Whisper. Mixed-language quality varies.

## Current limitations
- Speech selection uses word transcription and heuristic scoring, not an LLM understanding of viral potential.
- A centered 9:16 crop is used; speaker tracking is not implemented.
- Clips must contain sentence-end punctuation inferred by transcription, or end at the final segment.
- The subtitle burn-in requires an FFmpeg build with libass; font support affects Arabic rendering.
- No mobile cloud backend, upload endpoint, or hosted processing yet.
- No guarantee of a free unlimited server. CPU transcription may be slow.
- Only process videos you have rights to use.
