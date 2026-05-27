import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import ffmpeg
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from app.core.config import settings
from app.core.errors import (
    ChunkingFailedError,
    FFmpegNotAvailableError,
    MediaConversionError,
)

NORMALIZED_AUDIO_CODEC = "libmp3lame"
NORMALIZED_SAMPLE_RATE = 16_000
NORMALIZED_CHANNELS = 1

# 書き出し後の実サイズが想定より大きい場合に、少しずつ末尾を詰めて上限内へ収める。
_CHUNK_SIZE_SHRINK_MAX_ATTEMPTS = 48
_CHUNK_SIZE_FIT_MARGIN = 0.92


@dataclass(frozen=True)
class AudioChunk:
    """OpenAI API に個別アップロードする音声チャンクのメタデータ。"""

    index: int
    path: str
    start_seconds: float
    end_seconds: float
    size_bytes: int


def _get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)


def _ensure_ffmpeg_available() -> None:
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


def _tmp_dir(name: str) -> Path:
    base_dir = Path(__file__).resolve().parent
    directory = (base_dir / f"../tmp/{name}").resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _run_ffmpeg(stream, output_path: Path) -> None:
    try:
        stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode() if exc.stderr else str(exc)
        raise MediaConversionError(f"FFmpeg の変換に失敗しました: {stderr}") from exc

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise MediaConversionError("FFmpeg の出力ファイルが生成されませんでした")


def needs_chunking(size_bytes: int) -> bool:
    return size_bytes > settings.openai_max_upload_bytes


def _ms_to_seconds(ms: int) -> float:
    return round(ms / 1000.0, 3)


def _estimate_size_bytes(bytes_per_ms: float, duration_ms: int) -> int:
    return int(bytes_per_ms * duration_ms)


def _silence_gaps(
    audio: AudioSegment,
    start_ms: int,
    end_ms: int,
    min_silence_len_ms: int,
    silence_thresh_db_offset: int,
) -> list[tuple[int, int]]:
    """指定範囲内で、分割候補にできる無音区間を絶対ミリ秒で返す。"""

    segment = audio[start_ms:end_ms]
    if len(segment) == 0:
        return []

    silence_thresh = segment.dBFS - silence_thresh_db_offset
    nonsilent = detect_nonsilent(
        segment,
        min_silence_len=min_silence_len_ms,
        silence_thresh=silence_thresh,
    )

    gaps: list[tuple[int, int]] = []
    if not nonsilent:
        # 完全な無音区間なら、指定範囲全体を分割候補として扱う。
        return [(start_ms, end_ms)]

    if nonsilent[0][0] > 0:
        gaps.append((start_ms, start_ms + nonsilent[0][0]))

    for index in range(len(nonsilent) - 1):
        gap_start = start_ms + nonsilent[index][1]
        gap_end = start_ms + nonsilent[index + 1][0]
        if gap_end - gap_start >= min_silence_len_ms:
            gaps.append((gap_start, gap_end))

    last_nonsilent_end = start_ms + nonsilent[-1][1]
    if last_nonsilent_end < end_ms:
        gaps.append((last_nonsilent_end, end_ms))

    return gaps


def _pick_split_ms(
    gaps: list[tuple[int, int]],
    start_ms: int,
    target_end_ms: int,
    max_end_ms: int,
    keep_silence_ms: int,
) -> int | None:
    """上限内に収まる無音区間から、目標終了時刻に最も近い分割点を選ぶ。"""

    best_split: int | None = None
    best_distance = float("inf")

    for gap_start, gap_end in gaps:
        gap_length = gap_end - gap_start
        if gap_length <= keep_silence_ms * 2:
            split_ms = gap_start + gap_length // 2
        else:
            # 前後に少し無音を残し、単語や短い間が切れにくい位置を選ぶ。
            split_ms = gap_start + keep_silence_ms + (gap_length - keep_silence_ms * 2) // 2

        if split_ms <= start_ms or split_ms > max_end_ms:
            continue

        distance = abs(split_ms - target_end_ms)
        if distance < best_distance:
            best_distance = distance
            best_split = split_ms

    return best_split


def _find_split_ms(
    audio: AudioSegment,
    start_ms: int,
    duration_ms: int,
    bytes_per_ms: float,
) -> tuple[int, bool]:
    """次チャンクの終了位置と、時間ベース分割に落ちたかどうかを返す。"""

    remaining_ms = duration_ms - start_ms
    remaining_bytes = _estimate_size_bytes(bytes_per_ms, remaining_ms)

    if remaining_bytes <= settings.openai_max_upload_bytes:
        return (duration_ms, False)

    target_duration_ms = int(settings.chunk_target_bytes / bytes_per_ms)
    max_duration_ms = int(settings.chunk_max_bytes / bytes_per_ms)
    target_end_ms = min(start_ms + target_duration_ms, duration_ms)
    max_end_ms = min(start_ms + max_duration_ms, duration_ms)

    search_params = (
        (
            settings.chunk_min_silence_len_ms,
            settings.chunk_silence_thresh_db_offset,
        ),
        (
            settings.chunk_fallback_min_silence_len_ms,
            settings.chunk_fallback_silence_thresh_db_offset,
        ),
    )

    # まず通常条件で無音を探し、見つからなければ短めの無音にも広げて再探索する。
    for min_silence_len_ms, silence_thresh_db_offset in search_params:
        gaps = _silence_gaps(
            audio,
            start_ms,
            duration_ms,
            min_silence_len_ms,
            silence_thresh_db_offset,
        )
        split_ms = _pick_split_ms(
            gaps,
            start_ms,
            target_end_ms,
            max_end_ms,
            settings.chunk_keep_silence_ms,
        )
        if split_ms is not None:
            return (split_ms, False)

    # 無音が見つからない音声では、アップロード上限に収まる時間で機械的に切る。
    split_ms = max_end_ms
    if split_ms <= start_ms:
        split_ms = min(start_ms + max(1, max_duration_ms // 2), duration_ms)
    if split_ms <= start_ms:
        raise ChunkingFailedError("時間ベース分割位置を決定できませんでした")

    return (split_ms, True)


def _export_chunk(
    source_path: str,
    output_path: Path,
    start_seconds: float,
    duration_seconds: float,
) -> None:
    """元音声の指定範囲だけを、正規化済みMP3チャンクとして書き出す。"""

    stream = (
        ffmpeg.input(source_path, ss=start_seconds)
        .output(
            str(output_path),
            t=duration_seconds,
            acodec=NORMALIZED_AUDIO_CODEC,
            ar=NORMALIZED_SAMPLE_RATE,
            ac=NORMALIZED_CHANNELS,
        )
    )
    _run_ffmpeg(stream, output_path)


def _export_with_size_limit(
    source_path: str,
    output_path: Path,
    start_ms: int,
    end_ms: int,
) -> AudioChunk:
    """チャンクを書き出し、実ファイルサイズが上限を超えたら範囲を短縮する。"""

    start_seconds = _ms_to_seconds(start_ms)
    current_end_ms = end_ms

    for _ in range(_CHUNK_SIZE_SHRINK_MAX_ATTEMPTS):
        end_seconds = _ms_to_seconds(current_end_ms)
        duration_seconds = end_seconds - start_seconds
        if duration_seconds <= 0:
            raise ChunkingFailedError(
                "チャンクの長さが 0 以下になり、書き出せませんでした"
            )

        _export_chunk(source_path, output_path, start_seconds, duration_seconds)
        size_bytes = _get_file_size(str(output_path))

        if size_bytes <= settings.chunk_max_bytes:
            return AudioChunk(
                index=0,
                path=str(output_path),
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                size_bytes=size_bytes,
            )

        duration_ms = current_end_ms - start_ms
        if duration_ms <= 1:
            raise ChunkingFailedError(
                f"チャンクサイズ ({size_bytes} bytes) が上限 ({settings.chunk_max_bytes} bytes) を超え、"
                "これ以上短縮できませんでした"
            )

        measured_bpm = size_bytes / duration_ms
        if measured_bpm <= 0:
            raise ChunkingFailedError(
                "チャンクのビットレート推定が不正なため、サイズ上限に収められませんでした"
            )

        target_duration_ms = int(
            settings.chunk_max_bytes / measured_bpm * _CHUNK_SIZE_FIT_MARGIN
        )
        new_end_ms = start_ms + max(1, min(target_duration_ms, duration_ms - 1))
        if new_end_ms >= current_end_ms:
            new_end_ms = start_ms + max(1, duration_ms // 2)
        current_end_ms = new_end_ms

    raise ChunkingFailedError(
        f"チャンクサイズを上限 ({settings.chunk_max_bytes} bytes) 以下に収める再試行が "
        f"{_CHUNK_SIZE_SHRINK_MAX_ATTEMPTS} 回で尽きました"
    )


def create_chunks(normalized_path: str) -> list[AudioChunk]:
    """正規化済み音声をOpenAI APIのサイズ上限に収まる複数ファイルへ分割する。"""

    _ensure_ffmpeg_available()

    source_path = Path(normalized_path)
    if not source_path.is_file():
        raise ChunkingFailedError(f"音声ファイルが見つかりません: {normalized_path}")

    file_size = _get_file_size(normalized_path)
    if not needs_chunking(file_size):
        raise ChunkingFailedError(
            "分割不要なファイルに create_chunks が呼び出されました"
        )

    try:
        audio = AudioSegment.from_file(normalized_path)
    except Exception as exc:
        raise ChunkingFailedError(f"音声ファイルの読み込みに失敗しました: {exc}") from exc

    duration_ms = len(audio)
    if duration_ms <= 0:
        raise ChunkingFailedError("音声の長さが 0 です")

    bytes_per_ms = file_size / duration_ms
    chunks_dir = _tmp_dir("chunks")
    chunk_prefix = uuid4().hex
    chunks: list[AudioChunk] = []
    start_ms = 0
    index = 0

    while start_ms < duration_ms:
        end_ms, used_time_fallback = _find_split_ms(
            audio, start_ms, duration_ms, bytes_per_ms
        )
        output_path = chunks_dir / f"{chunk_prefix}_{index:03d}.mp3"

        chunk = _export_with_size_limit(
            normalized_path,
            output_path,
            start_ms,
            end_ms,
        )
        chunks.append(
            AudioChunk(
                index=index,
                path=chunk.path,
                start_seconds=chunk.start_seconds,
                end_seconds=chunk.end_seconds,
                size_bytes=chunk.size_bytes,
            )
        )

        actual_end_ms = int(chunk.end_seconds * 1000)
        if actual_end_ms >= duration_ms:
            break

        overlap_ms = 0
        if used_time_fallback:
            # 無音で切れなかった場合だけ、設定された重なりを入れて聞き落としを抑える。
            overlap_ms = int(settings.chunk_time_fallback_overlap_seconds * 1000)
        if overlap_ms > 0:
            start_ms = max(actual_end_ms - overlap_ms, start_ms + 1)
        else:
            start_ms = max(actual_end_ms, start_ms + 1)
        index += 1

        if index > 10_000:
            raise ChunkingFailedError("チャンク数が上限を超えました")

    if not chunks:
        raise ChunkingFailedError("チャンクを 1 つも生成できませんでした")

    return chunks
