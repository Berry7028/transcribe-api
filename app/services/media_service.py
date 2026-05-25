import os
import shutil
import subprocess

import ffmpeg
from pathlib import Path
from uuid import uuid4

from app.core.errors import FFmpegNotAvailableError, MediaConversionError

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".3gp",
}

NORMALIZED_AUDIO_CODEC = "libmp3lame"
NORMALIZED_SAMPLE_RATE = 16_000
NORMALIZED_CHANNELS = 1


def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)


def _tmp_dir(name: str) -> Path:
    base_dir = Path(__file__).resolve().parent
    directory = (base_dir / f"../tmp/{name}").resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _run_ffmpeg(stream: ffmpeg.nodes.OutputStream, output_path: Path) -> None:
    try:
        stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode() if exc.stderr else str(exc)
        raise MediaConversionError(f"FFmpeg の変換に失敗しました: {stderr}") from exc

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise MediaConversionError("FFmpeg の出力ファイルが生成されませんでした")


def ensure_ffmpeg_available() -> None:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise FFmpegNotAvailableError()

    try:
        subprocess.run(
            [ffmpeg_path, "-version"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FFmpegNotAvailableError("ffmpeg を実行できません") from exc


def extract_audio(file_path: str) -> str:
    extracted_dir = _tmp_dir("extracted")
    output_path = extracted_dir / f"{uuid4().hex}.wav"

    stream = (
        ffmpeg.input(file_path)
        .output(
            str(output_path),
            vn=None,
            acodec="pcm_s16le",
            ar=NORMALIZED_SAMPLE_RATE,
            ac=NORMALIZED_CHANNELS,
        )
    )
    _run_ffmpeg(stream, output_path)
    return str(output_path)


def normalize_audio(file_path: str) -> str:
    normalized_dir = _tmp_dir("normalized")
    output_path = normalized_dir / f"{uuid4().hex}.mp3"

    stream = (
        ffmpeg.input(file_path)
        .output(
            str(output_path),
            acodec=NORMALIZED_AUDIO_CODEC,
            ar=NORMALIZED_SAMPLE_RATE,
            ac=NORMALIZED_CHANNELS,
        )
    )
    _run_ffmpeg(stream, output_path)
    return str(output_path)


def prepare_audio(input_path: str) -> dict[str, str | int]:
    ensure_ffmpeg_available()

    extension = Path(input_path).suffix.lower()
    if extension in VIDEO_EXTENSIONS:
        extracted_path = extract_audio(input_path)
        normalized_path = normalize_audio(extracted_path)
    else:
        normalized_path = normalize_audio(input_path)

    return {
        "normalized_path": normalized_path,
        "size_bytes": get_file_size(normalized_path),
    }
