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

# Whisper API に送る前に、音声は同じサンプルレート・チャンネル数へ正規化する。
NORMALIZED_AUDIO_CODEC = "libmp3lame"
NORMALIZED_SAMPLE_RATE = 16_000
NORMALIZED_CHANNELS = 1


def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)


def get_duration_seconds(file_path: str) -> float:
    try:
        probe = ffmpeg.probe(file_path)
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode() if exc.stderr else str(exc)
        raise MediaConversionError(f"音声ファイルの長さを取得できませんでした: {stderr}") from exc

    duration = probe.get("format", {}).get("duration")
    if duration is None:
        raise MediaConversionError("音声ファイルの長さを取得できませんでした")

    return float(duration)


def _tmp_dir(name: str) -> Path:
    # app/tmp 配下に用途別ディレクトリを作ることで、削除対象を追いやすくする。
    base_dir = Path(__file__).resolve().parent
    directory = (base_dir / f"../tmp/{name}").resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _run_ffmpeg(stream: ffmpeg.nodes.OutputStream, output_path: Path) -> None:
    # ffmpeg-python の例外には標準エラーが入るため、変換失敗時の診断に含める。
    try:
        stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode() if exc.stderr else str(exc)
        raise MediaConversionError(f"FFmpeg の変換に失敗しました: {stderr}") from exc

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise MediaConversionError("FFmpeg の出力ファイルが生成されませんでした")


def ensure_ffmpeg_available() -> None:
    # pydub/ffmpeg-python の遅い失敗より先に、実行ファイルの有無を明示的に確認する。
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
    """動画ファイルからモノラル16kHzのWAV音声を抽出する。"""

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
    """OpenAI API のアップロードに使うMP3へ正規化する。"""

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
    """入力ファイルを文字起こし可能な音声ファイルへ変換する。"""

    ensure_ffmpeg_available()

    extension = Path(input_path).suffix.lower()
    extracted_path = None
    if extension in VIDEO_EXTENSIONS:
        # 動画は一度WAVへ抽出してからMP3化し、以降の処理を音声ファイルに統一する。
        extracted_path = extract_audio(input_path)
        normalized_path = normalize_audio(extracted_path)
    else:
        normalized_path = normalize_audio(input_path)

    result: dict[str, str | int] = {
        "normalized_path": normalized_path,
        "size_bytes": get_file_size(normalized_path),
    }
    if extracted_path is not None:
        result["extracted_path"] = extracted_path
    return result
