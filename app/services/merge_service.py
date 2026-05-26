import re
from dataclasses import dataclass

_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class ChunkTranscription:
    index: int
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class ResponseChunk:
    index: int
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class MergedTranscription:
    text: str
    duration_seconds: float
    chunks: list[ResponseChunk]


def normalize_text(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    return _WHITESPACE_RE.sub(" ", stripped)


def _sorted_chunks(
    chunk_transcriptions: list[ChunkTranscription],
) -> list[ChunkTranscription]:
    if not chunk_transcriptions:
        raise ValueError("結合するチャンクの文字起こし結果がありません")

    return sorted(chunk_transcriptions, key=lambda chunk: chunk.index)


def _build_response_chunks(
    chunk_transcriptions: list[ChunkTranscription],
) -> list[ResponseChunk]:
    return [
        ResponseChunk(
            index=chunk.index,
            start_seconds=chunk.start_seconds,
            end_seconds=chunk.end_seconds,
            text=normalize_text(chunk.text),
        )
        for chunk in chunk_transcriptions
    ]


def _merge_text(chunk_transcriptions: list[ChunkTranscription]) -> str:
    parts: list[str] = []
    for chunk in chunk_transcriptions:
        normalized = normalize_text(chunk.text)
        if normalized:
            parts.append(normalized)
    return " ".join(parts)


def _duration_seconds(chunk_transcriptions: list[ChunkTranscription]) -> float:
    return max(chunk.end_seconds for chunk in chunk_transcriptions)


def merge_chunk_transcriptions(
    chunk_transcriptions: list[ChunkTranscription],
) -> MergedTranscription:
    ordered = _sorted_chunks(chunk_transcriptions)
    response_chunks = _build_response_chunks(ordered)

    return MergedTranscription(
        text=_merge_text(ordered),
        duration_seconds=_duration_seconds(ordered),
        chunks=response_chunks,
    )
