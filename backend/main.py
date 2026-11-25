from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import json, os, re, subprocess, math

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent.parent
BACKEND = BASE / "backend"
OUTPUT = BASE / "output"
ASSETS = BASE / "assets"
OUTPUT.mkdir(exist_ok=True)
(ASSETS / "images").mkdir(parents=True, exist_ok=True)
(ASSETS / "audio").mkdir(parents=True, exist_ok=True)
load_dotenv(BASE / ".env")

app = FastAPI(title="AI YouTube Studio", version="0.1.0")
app.mount("/assets", StaticFiles(directory=str(ASSETS)), name="assets")
app.mount("/static", StaticFiles(directory=str(BASE / "frontend")), name="static")

class ScriptRequest(BaseModel):
    script: str
    target_minutes: int = 20

class MetadataRequest(BaseModel):
    title: str = ""
    script: str

class RenderRequest(BaseModel):
    script: str
    target_minutes: int = 20
    image_dir: str = "assets/images"
    audio_file: str = "assets/audio/narration.mp3"
    output: str = "output/documentary.mp4"

@app.get("/")
def home():
    return FileResponse(BASE / "frontend" / "index.html")

@app.get("/api/health")
def health():
    ffmpeg = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).returncode == 0 if _has_ffmpeg() else False
    return {"ok": True, "app": "AI YouTube Studio", "ffmpeg_available": ffmpeg,
            "youtube_credentials_present": (BACKEND / "client_secret.json").exists()}

def _has_ffmpeg():
    import shutil
    return shutil.which("ffmpeg") is not None

def _ollama(prompt: str):
    url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/") + "/api/generate"
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    try:
        r = requests.post(url, json={"model": model, "prompt": prompt, "stream": False}, timeout=90)
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception:
        return None

@app.post("/api/metadata")
def metadata(req: MetadataRequest):
    clean_title = req.title.strip() or "The Untold Story"
    prompt = f"""You are a YouTube documentary channel editor. Based only on the script below, return valid JSON with keys title, description, tags (array), hashtags (array). Write natural Hindi if the script is primarily Hindi, otherwise English. Be accurate, avoid fake claims, keyword stuffing, and misleading clickbait. Description should sound human and include a concise summary and a viewer question. Title under 100 characters.\nSCRIPT:\n{req.script[:12000]}"""
    answer = _ollama(prompt)
    if answer:
        try:
            match = re.search(r"\{.*\}", answer, re.S)
            data = json.loads(match.group(0) if match else answer)
            return data
        except Exception:
            pass
    excerpt = re.sub(r"\s+", " ", req.script).strip()[:500]
    return {
        "title": clean_title[:100],
        "description": f"{clean_title}\n\n{excerpt}\n\nइस कहानी के बारे में आपकी क्या राय है? कमेंट में बताइए। वीडियो पसंद आए तो चैनल को सब्सक्राइब करें।\n\n#Documentary #History #Hindi",
        "tags": ["Hindi documentary", "history", "storytelling", "educational"],
        "hashtags": ["#HindiDocumentary", "#History", "#Storytelling"],
        "note": "Ollama was unavailable; generated a basic fallback. Add a local Ollama model for AI-written metadata."
    }

def split_into_scenes(script: str, target_minutes: int):
    # Split by paragraphs first; then sentence groups. Approx. 125 spoken words/min.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    if not paragraphs:
        paragraphs = [s.strip() for s in re.split(r"(?<=[.!?।])\s+", script) if s.strip()]
    if not paragraphs:
        return []
    scenes = []
    max_words = max(45, min(110, round(target_minutes * 125 / max(1, math.ceil(target_minutes * 125 / 75)))))
    current = []
    count = 0
    for para in paragraphs:
        words = len(para.split())
        if current and count + words > max_words:
            scenes.append(" ".join(current)); current=[]; count=0
        current.append(para); count += words
    if current: scenes.append(" ".join(current))
    total_words = len(script.split())
    total_seconds = max(target_minutes * 60, round(total_words / 125 * 60))
    duration = total_seconds / max(1, len(scenes))
    return [{"scene": i+1, "duration_seconds": round(duration, 1),
             "narration": part,
             "visual_prompt": f"Create an original cinematic documentary visual illustrating: {part[:260]}",
             "image_file": f"scene_{i+1:03d}.jpg"} for i, part in enumerate(scenes)]

@app.post("/api/scenes")
def scenes(req: ScriptRequest):
    if len(req.script.strip()) < 30:
        raise HTTPException(400, "Please provide a longer script.")
    return {"scenes": split_into_scenes(req.script, max(1, min(req.target_minutes, 180))),
            "word_count": len(req.script.split()),
            "estimated_minutes_at_125_wpm": round(len(req.script.split()) / 125, 1)}

@app.get("/api/youtube/status")
def youtube_status():
    return {"connected": (BACKEND / "token.json").exists(),
            "credentials_present": (BACKEND / "client_secret.json").exists()}

@app.get("/api/youtube/connect")
def youtube_connect():
    secret = BACKEND / "client_secret.json"
    if not secret.exists():
        raise HTTPException(400, "Add your Google OAuth Desktop client_secret.json to the backend folder first.")
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(secret), ["https://www.googleapis.com/auth/youtube.upload"])
        creds = flow.run_local_server(port=0, prompt="consent")
        (BACKEND / "token.json").write_text(creds.to_json(), encoding="utf-8")
        return {"connected": True, "message": "YouTube account connected. You can close the browser tab."}
    except Exception as e:
        raise HTTPException(500, f"YouTube OAuth failed: {e}")

def youtube_service():
    token = BACKEND / "token.json"
    if not token.exists():
        raise HTTPException(401, "Connect YouTube first.")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(token), ["https://www.googleapis.com/auth/youtube.upload"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)

@app.post("/api/youtube/upload")
def youtube_upload(video: UploadFile = File(...), title: str = Form(...),
                   description: str = Form(""), tags: str = Form(""),
                   publish_at: str = Form(""), thumbnail: Optional[UploadFile] = File(None)):
    if not video.filename.lower().endswith((".mp4", ".mov", ".m4v")):
        raise HTTPException(400, "Please upload an MP4, MOV or M4V video.")
    temp = OUTPUT / f"upload_{re.sub(r'[^a-zA-Z0-9._-]', '_', video.filename)}"
    with temp.open("wb") as f:
        f.write(video.file.read())
    body = {"snippet": {"title": title[:100], "description": description[:5000],
                        "tags": [t.strip() for t in tags.split(",") if t.strip()][:500],
                        "categoryId": "27"},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}
    if publish_at.strip():
        try:
            dt = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
            if dt.tzinfo is None or dt <= datetime.now(timezone.utc):
                raise ValueError("Use a future date/time including timezone, e.g. 2026-12-01T18:30:00+05:30")
            body["status"]["publishAt"] = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            body["status"]["privacyStatus"] = "private"
        except ValueError as e:
            temp.unlink(missing_ok=True)
            raise HTTPException(400, str(e))
    try:
        from googleapiclient.http import MediaFileUpload
        service = youtube_service()
        result = service.videos().insert(part="snippet,status", body=body,
            media_body=MediaFileUpload(str(temp), chunksize=-1, resumable=True)).execute()
        if thumbnail and thumbnail.filename:
            thumb_path = OUTPUT / "thumbnail_upload"
            thumb_path.write_bytes(thumbnail.file.read())
            service.thumbnails().set(videoId=result["id"], media_body=MediaFileUpload(str(thumb_path))).execute()
            thumb_path.unlink(missing_ok=True)
        return {"video_id": result["id"], "url": f"https://www.youtube.com/watch?v={result['id']}",
                "status": body["status"], "message": "Upload complete. Check YouTube Studio for processing."}
    except Exception as e:
        raise HTTPException(500, f"YouTube upload failed: {e}")
    finally:
        temp.unlink(missing_ok=True)

@app.post("/api/render")
def render(req: RenderRequest):
    if not _has_ffmpeg():
        raise HTTPException(400, "FFmpeg is not installed or not on PATH. Install FFmpeg and restart the app.")
    image_dir = (BASE / req.image_dir).resolve()
    audio = (BASE / req.audio_file).resolve()
    output = (BASE / req.output).resolve()
    if not image_dir.is_relative_to(BASE) or not audio.is_relative_to(BASE) or not output.is_relative_to(BASE):
        raise HTTPException(400, "Paths must stay inside the project folder.")
    images = sorted([p for p in image_dir.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")])
    if not images:
        raise HTTPException(400, f"No images found in {image_dir}. Add scene_001.jpg, scene_002.jpg, etc.")
    if not audio.exists():
        raise HTTPException(400, f"Narration audio not found: {audio}. Add narration.mp3.")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Build a concat file with each still held for equal segments; narration sets final duration.
    duration = max(1, req.target_minutes * 60 / len(images))
    concat = OUTPUT / "images.txt"
    with concat.open("w", encoding="utf-8") as f:
        for img in images:
            f.write(f"file '{str(img).replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")
            f.write(f"duration {duration:.3f}\n")
        f.write(f"file '{str(images[-1])}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
           "-i", str(audio), "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-r", "30",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(output)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    concat.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise HTTPException(500, "FFmpeg render failed: " + proc.stderr[-1800:])
    return {"rendered": True, "file": str(output.relative_to(BASE)).replace("\\", "/"),
            "download_url": "/api/download/" + output.name, "image_count": len(images)}

@app.get("/api/download/{filename}")
def download(filename: str):
    path = (OUTPUT / filename).resolve()
    if not path.is_relative_to(OUTPUT.resolve()) or not path.exists():
        raise HTTPException(404, "File not found.")
    return FileResponse(path, media_type="video/mp4", filename=path.name)