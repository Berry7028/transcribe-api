import os
from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
from uuid import uuid4

from services.media_service import prepare_audio


# 許可する拡張子のリスト

ALLOWED_EXTENSIONS = {
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".m4a",
    ".wav",
    ".webm",
    ".mov",
    ".avi",
    ".mkv",
    ".aac",
    ".flac",
    ".ogg",
    ".wma",
    ".3gp",
    ".opus"
}

router = APIRouter()

@router.post("/transcriptions")
async def create_upload_file(file: UploadFile = File(...)):
    base_dir = Path(__file__).resolve().parent
    upload_dir = (base_dir / "../../tmp/uploads").resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
      raise HTTPException(
        status_code=400,
        detail=f"許可されていない拡張子です。許可されている形式: {list(ALLOWED_EXTENSIONS)}"
      )

    suffix = Path(file.filename or "").suffix
    saved_path = upload_dir / f"{uuid4().hex}{suffix}"

    with saved_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    prepared = prepare_audio(str(saved_path))

    return {
        "filename": file.filename,
        "saved_path": str(saved_path),
        "normalized_path": prepared["normalized_path"],
        "size_bytes": prepared["size_bytes"],
    }