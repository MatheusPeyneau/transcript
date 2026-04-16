import os
import base64
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
import yt_dlp

app = FastAPI()

# Configuração de CORS para aceitar sua extensão
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, substitua pelo ID da sua extensão
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carrega o modelo Whisper (o "base" é um ótimo equilíbrio entre velocidade e precisão)
model_size = "base"
model = WhisperModel(model_size, device="cpu", compute_type="int8")

@app.post("/transcrever")
async def transcrever(request: Request):
    data = await request.json()
    video_url = data.get("videoUrl")
    base64_data = data.get("base64")
    file_id = str(uuid.uuid4())
    temp_audio = f"temp_{file_id}.mp3"

    try:
        if base64_data:
            # Lógica para TikTok (Base64)
            video_bytes = base64.b64decode(base64_data)
            with open(temp_audio, "wb") as f:
                f.write(video_bytes)
        elif video_url:
            # Lógica para Instagram (URL via yt-dlp)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_audio,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

        # Transcrição com Whisper
        segments, info = model.transcribe(temp_audio, beam_size=5)
        text = " ".join([segment.text for segment in segments])

        # Limpeza
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

        return {"status": "success", "transcription": text.strip()}

    except Exception as e:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))