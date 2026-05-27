import asyncio
import os
from fastapi import APIRouter, File, UploadFile
from pathlib import Path
from uuid import uuid4

from app.core.errors import InvalidRequestError, UnsupportedFileTypeError
from app.schemas.transcription import TranscriptionResponse
from app.services.transcription_service import transcribe_file


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
async def create_upload_file(file: UploadFile = File(...)) -> TranscriptionResponse:
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

    return await asyncio.to_thread(transcribe_file, str(saved_path))
