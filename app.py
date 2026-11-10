"""AutoClips AI — deployable Gradio prototype for free-tier CPU hosting."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "engine" / "clipper.py"


def process_video(video, count, min_seconds, max_seconds, subtitles, model):
    if not video:
        raise gr.Error("ارفع فيديو أولًا.")
    if int(max_seconds) <= int(min_seconds):
        raise gr.Error("مدة النهاية لازم تكون أكبر من مدة البداية.")
    source = Path(video)
    if source.is_file() and source.stat().st_size > 150 * 1024 * 1024:
        raise gr.Error("حجم الفيديو أكبر من 150 ميجابايت. جرّب ملفًا أصغر.")
    if not source.is_file():
        raise gr.Error("ملف الفيديو غير متاح.")
    if source.suffix.lower() not in {".mp4", ".mov", ".webm", ".mkv"}:
        raise gr.Error("الصيغة غير مدعومة. استخدم MP4 أو MOV أو WebM أو MKV.")
    # Keep temporary outputs for the session; Gradio copies returned files into its cache.
    output = Path(tempfile.mkdtemp(prefix="autoclips_"))
    command = [
        sys.executable, str(ENGINE), str(source),
        "--output", str(output), "--count", str(int(count)),
        "--min-seconds", str(int(min_seconds)),
        "--max-seconds", str(int(max_seconds)), "--model", model,
    ]
    if subtitles:
        command.append("--subtitles")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        raise gr.Error("انتهت مهلة المعالجة. جرّب فيديو أقصر.")
    if result.returncode:
        detail = (result.stderr or result.stdout)[-1800:]
        raise gr.Error("فشلت المعالجة: " + detail)
    clips = sorted(output.glob("clip_*.mp4"))
    if not clips:
        raise gr.Error("لم نجد مقاطع مناسبة في الفيديو. جرّب فيديو أطول أو قلّل الحد الأدنى.")
    meta = output / "clips.json"
    description = f"تم إنشاء {len(clips)} شورتس."
    if meta.exists():
        info = json.loads(meta.read_text(encoding="utf-8"))
        description += "\n" + "\n".join(
            f"المقطع {i+1}: {row['start']:.1f}–{row['end']:.1f} ثانية"
            for i, row in enumerate(info)
        )
    return description, [str(p) for p in clips], str(clips[0])


with gr.Blocks(title="AutoClips AI | بودكاست إلى شورتس") as demo:
    gr.Markdown("# ✂️ AutoClips AI\nحوّل البودكاست العربي أو الإنجليزي إلى شورتس عمودية. **نسخة تجريبية**: الاختيار مبني على تفريغ الكلام وقواعد مبدئية، وليس تحليلًا دلاليًا متقدمًا.")
    gr.Markdown("قد تستغرق المعالجة وقتًا طويلًا على الخوادم المجانية، وقد تتوقف عند نفاد الموارد.")
    video = gr.Video(label="ارفع فيديو بودكاست", sources=["upload"])
    with gr.Row():
        count = gr.Slider(1, 5, value=3, step=1, label="عدد الشورتس")
        model = gr.Dropdown(["tiny", "base"], value="tiny", label="دقة تفريغ الكلام")
    with gr.Row():
        min_seconds = gr.Slider(10, 60, value=15, step=5, label="أقل مدة (ثانية)")
        max_seconds = gr.Slider(30, 90, value=60, step=5, label="أكبر مدة (ثانية)")
    subtitles = gr.Checkbox(value=True, label="إضافة ترجمة على الفيديو")
    gr.Markdown("⚠️ النسخة التجريبية مخصصة للفيديوهات غير الخاصة فقط. الملفات المرفوعة قد تبقى مؤقتًا في ذاكرة التخزين على الاستضافة.")
    run = gr.Button("ابدأ التقطيع التلقائي", variant="primary")
    status = gr.Textbox(label="نتيجة المعالجة", lines=4)
    downloads = gr.File(label="تنزيل الشورتس", file_count="multiple")
    preview = gr.Video(label="معاينة أول شورت")
    run.click(process_video, inputs=[video, count, min_seconds, max_seconds, subtitles, model],
              outputs=[status, downloads, preview], concurrency_limit=1)

if __name__ == "__main__":
    demo.queue(max_size=3).launch(max_file_size="150mb")
