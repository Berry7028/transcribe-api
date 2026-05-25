# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Transcribe API — a Python/FastAPI backend that accepts audio/video file uploads, processes them with ffmpeg, and transcribes via OpenAI Whisper API.

### Running the dev server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Key endpoints

- `GET /health` — health check (no auth needed)
- `POST /api/transcriptions` — upload audio/video file, returns transcription JSON

### Environment variables

Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Without it, transcription requests return `missing_api_key` error (upload + audio processing still work).

### System dependencies

- **Python >= 3.11** (pre-installed in cloud VM)
- **ffmpeg** (pre-installed in cloud VM) — required for audio extraction/normalization; the app raises `FFmpegNotAvailableError` if missing

### Notes

- No tests exist yet (`pytest` is planned per `TODO.md`).
- No linter configuration exists in `pyproject.toml`; no lint command is available.
- Uploaded/processed files are written to `app/tmp/` subdirectories (gitignored via `tmp/`).
- The `pip install -e .` editable install is required so that `app.*` imports resolve correctly.
