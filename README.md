# AI YouTube Studio (local-first starter)

A local-first starter app for a two-part workflow:
1. **Creator Studio** — prepare metadata, authenticate with YouTube, upload videos, and schedule publishing.
2. **Documentary Maker** — turn a supplied script into timed scenes, attach your own/generated images and narration, and render a 1080p MP4 with FFmpeg.

This is a real starter implementation, not a hosted service. It runs on your Windows PC. You control your Google account and API keys.

## Requirements
- Python 3.10+
- FFmpeg installed and available on PATH (`ffmpeg -version`)
- A Google Cloud project with **YouTube Data API v3** enabled and OAuth Desktop credentials downloaded as `client_secret.json`.
- Optional: Ollama installed locally with a model pulled, e.g. `ollama pull llama3.2`. The app still works without Ollama using a deterministic metadata fallback.

## Setup (Windows PowerShell)
```powershell
cd ai-youtube-studio
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Put your Google OAuth Desktop JSON at backend/client_secret.json
uvicorn backend.main:app --reload
```
Open http://127.0.0.1:8000

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## YouTube OAuth setup
1. Open Google Cloud Console and create/select a project.
2. Enable **YouTube Data API v3**.
3. Configure OAuth consent screen (External for a personal test app; add your Google account as a test user if required).
4. Create OAuth client ID → Desktop app.
5. Download JSON and save as `backend/client_secret.json`.
6. In the app, click **Connect YouTube**. A browser window opens for consent. Token is stored locally in `backend/token.json`.

Uploads are private by default. Scheduling requires a future date/time and uses YouTube's `publishAt`. Your channel/account may need to meet YouTube's API and feature requirements. The first API project may be subject to audit/verification restrictions. Never share `client_secret.json` or `token.json`.

## First workflow
1. Paste your documentary script into Documentary Maker.
2. Click **Create scene plan**. The app splits the script into scene-sized sections.
3. Put image files in `assets/images/` named `scene_001.jpg`, `scene_002.jpg`, etc. (or choose images in the browser UI and save them to the matching names manually).
4. Add narration audio at `assets/audio/narration.mp3`.
5. Click **Render 1080p**. FFmpeg makes a 1920x1080 MP4 with still-image motion and narration.
6. In Creator Studio, select the rendered MP4, generate metadata, connect YouTube, and upload or schedule.

### Important rendering note
The first renderer uses still images with slow zoom/pan (Ken Burns-style) and one narration track. It is intentionally simple and dependable. It does not yet synthesize a full voiceover or generate images by itself. Those are the next integrations; use image/audio services only after checking their commercial-use terms. Add scene-specific audio and richer animations in later versions.

## API endpoints
- `GET /api/health`
- `POST /api/metadata` `{ "title": "...", "script": "..." }`
- `POST /api/scenes` `{ "script": "...", "target_minutes": 20 }`
- `GET /api/youtube/status`
- `GET /api/youtube/connect`
- `POST /api/youtube/upload` multipart fields: `video`, `title`, `description`, `tags` (comma-separated), `publish_at` (optional ISO datetime with timezone, e.g. `2026-12-01T18:30:00+05:30`), `thumbnail` (optional image)
- `POST /api/render` `{ "script": "...", "target_minutes": 20, "image_dir": "assets/images", "audio_file": "assets/audio/narration.mp3", "output": "output/documentary.mp4" }`

## Safety and publishing
The app does not auto-publish without an explicit upload action. Review every script, image, audio track, title and description. Do not reuse another creator's footage, script, thumbnail, or music. AI-generated content is not automatically copyright-free; check each provider's license. Disclose realistic synthetic/altered content when YouTube requires it.
x
# ai-youtube-studio2
This is  ai saas which is used for ai video genration ,audio genration,with automated with youtube so it will be downloaded ,it also provide the dashboard to users
