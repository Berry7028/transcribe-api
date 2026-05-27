import os
import asyncio
from fastapi import APIRouter, File, UploadFile
from pathlib import Path
from uuid import uuid4

from app.core.errors import InvalidRequestError, UnsupportedFileTypeError
from app.services.media_service import prepare_audio
from app.services.openai_service import transcribe_audio


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
    ".opus",
}

router = APIRouter()

@router.post("/transcriptions")
async def create_upload_file(file: UploadFile = File(...)):
    base_dir = Path(__file__).resolve().parent
    upload_dir = (base_dir / "../../tmp/uploads").resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or ""
    if not filename:
        raise InvalidRequestError("ファイル名が指定されていません")

    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(ALLOWED_EXTENSIONS)

    suffix = Path(filename).suffix
    saved_path = upload_dir / f"{uuid4().hex}{suffix}"

    with saved_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    prepared = await asyncio.to_thread(prepare_audio, str(saved_path))
    normalized_path = str(prepared["normalized_path"])
    text = await asyncio.to_thread(transcribe_audio, normalized_path)

    return {
        "filename": filename,
        "saved_path": str(saved_path),
        "normalized_path": normalized_path,
        "size_bytes": prepared["size_bytes"],
        "text": text,
    }
