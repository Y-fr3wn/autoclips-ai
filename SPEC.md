# AutoClips AI — Podcast clipping specification

## Goal
Mobile-first online tool that turns long spoken-word videos into short clips, in Arabic and English, without paid subscriptions during prototyping.

## Language support
- Arabic, English, and mixed-language conversations.
- Automatic speech language detection.
- Preserve spoken language in generated subtitles.
- Use word-level timestamps where supported; otherwise sentence-level timing and manual correction.

## Pipeline (planned, not yet deployed)
1. Upload media with limits and validate format/size.
2. Extract audio with FFmpeg.
3. Transcribe with Whisper or faster-whisper; generate timestamps.
4. Group utterances into coherent topics and score candidates by hook, completeness, and clarity.
5. Trim clips at natural speech boundaries; allow manual adjustments.
6. Crop/reframe 9:16, starting with centered crop and later speaker tracking.
7. Burn in subtitles with Arabic shaping and English support.
8. Export MP4 clips and offer mobile downloads.

## Acceptance criteria
- Upload a short Arabic sample and an English sample.
- Generate at least one downloadable MP4 clip from each.
- No cut in the middle of a word.
- Subtitles readable and synchronized.
- Show errors clearly if a free processing quota is exhausted.

## Current status
Only the front-end video preview and manual time-range preview are implemented. No automatic clip generation, AI processing, export, or hosted backend yet.

## Cost constraints
Static hosting can be free; GPU/CPU-heavy server processing has quotas and is not guaranteed free indefinitely. Never require payment without user approval.
