"""AutoClips AI — deployable Gradio prototype for free-tier CPU hosting."""
import json
import shutil
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
    if not source.is_file():
        raise gr.Error("ملف الفيديو غير متاح.")
    # FFmpeg determines supported input containers/codecs. Do not restrict by extension.
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(source)], capture_output=True, text=True)
    if probe.returncode:
        raise gr.Error("تعذر قراءة الفيديو. تأكد أن الملف فيديو صالح.")
    try:
        duration = float(probe.stdout.strip())
    except ValueError:
        raise gr.Error("تعذر معرفة مدة الفيديو.")
    if duration <= 0 or duration > 12 * 60:
        raise gr.Error("الحد الأقصى لمدة الفيديو 12 دقيقة.")
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
        shutil.rmtree(output, ignore_errors=True)
        raise gr.Error("انتهت مهلة المعالجة. جرّب فيديو أقصر.")
    if result.returncode:
        detail = (result.stderr or result.stdout)[-1800:]
        shutil.rmtree(output, ignore_errors=True)
        raise gr.Error("فشلت المعالجة: " + detail)
    clips = sorted(output.glob("clip_*.mp4"))
    if not clips:
        shutil.rmtree(output, ignore_errors=True)
        raise gr.Error("لم نجد مقاطع مناسبة في الفيديو. جرّب فيديو أطول أو قلّل الحد الأدنى.")
    meta = output / "clips.json"
    description = f"تم إنشاء {len(clips)} شورتس."
    if meta.exists():
        info = json.loads(meta.read_text(encoding="utf-8"))
        description += "\n" + "\n".join(
            f"المقطع {i+1}: {row['start']:.1f}–{row['end']:.1f} ثانية"
            for i, row in enumerate(info)
        )
    archive = shutil.make_archive(str(output / "autoclips_shorts"), "zip", root_dir=output, base_dir=".")
    return description, [str(p) for p in clips], str(clips[0]), archive


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
    gr.Markdown("⏱️ ارفع فيديو حتى 12 دقيقة. حجم الملف يعتمد على قدرة الاستضافة؛ لا يوجد حد تطبيقي ثابت بالميجابايت.")
    gr.Markdown("⚠️ النسخة التجريبية مخصصة للفيديوهات غير الخاصة فقط. الملفات المرفوعة قد تبقى مؤقتًا في ذاكرة التخزين على الاستضافة.")
    run = gr.Button("ابدأ التقطيع التلقائي", variant="primary")
    status = gr.Textbox(label="نتيجة المعالجة", lines=4)
    downloads = gr.File(label="تنزيل الشورتس", file_count="multiple")
    preview = gr.Video(label="معاينة أول شورت")
    zip_download = gr.File(label="تنزيل جميع الشورتس ZIP")
    run.click(process_video, inputs=[video, count, min_seconds, max_seconds, subtitles, model],
              outputs=[status, downloads, preview, zip_download], concurrency_limit=1)

if __name__ == "__main__":
    demo.queue(max_size=3).launch()
