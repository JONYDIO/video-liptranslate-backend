# backend.py
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import shutil
import os
import whisper
from googletrans import Translator
import asyncio
import edge_tts

app = FastAPI()

# إنشاء مجلدات لتخزين الملفات
os.makedirs("input", exist_ok=True)
os.makedirs("output", exist_ok=True)

# تحميل نموذج Whisper
model = whisper.load_model("medium")
translator = Translator()

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    input_path = f"input/{file.filename}"
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1️⃣ تحويل الصوت العربي إلى نص
    result = model.transcribe(input_path, language="ar")
    arabic_text = result["text"]

    # 2️⃣ ترجمة النص إلى الإنجليزية
    english_text = translator.translate(arabic_text, src='ar', dest='en').text

    # 3️⃣ تحويل النص الإنجليزي إلى صوت TTS
    tts_path = f"output/english_audio.mp3"
    communicate = edge_tts.Communicate(english_text, "en-US-AriaNeural")
    await communicate.save(tts_path)

    # 4️⃣ مؤقتًا نعيد الفيديو الأصلي إذا لا يوجد GPU للـ Lip-sync
    final_path = f"output/final_video.mp4"
    shutil.copy(input_path, final_path)

    return {"status": "done", "video_url": f"/download/{file.filename}"}

@app.get("/download/{filename}")
async def download_video(filename: str):
    final_path = f"output/final_video.mp4"
    return FileResponse(final_path, media_type="video/mp4", filename="VideoTranslated.mp4")
