from app.schemas.transcription import TranscriptionResponse
from app.services import transcription_service
from app.services.chunk_service import AudioChunk


def test_transcribe_file_returns_single_file_response_and_cleans_up(monkeypatch):
    cleanup_calls = []

    monkeypatch.setattr(
        transcription_service,
        "prepare_audio",
        lambda path: {"normalized_path": "/tmp/normalized.mp3", "size_bytes": 42},
    )
    monkeypatch.setattr(transcription_service, "needs_chunking", lambda size: False)
    monkeypatch.setattr(transcription_service, "get_duration_seconds", lambda path: 12.3456)
    monkeypatch.setattr(transcription_service, "transcribe_audio", lambda path: "文字起こし結果")
    monkeypatch.setattr(transcription_service, "cleanup_temp_files", lambda paths: cleanup_calls.append(paths))

    result = transcription_service.transcribe_file("/tmp/upload.wav")

    assert isinstance(result, TranscriptionResponse)
    assert result.text == "文字起こし結果"
    assert result.duration_seconds == 12.346
    assert result.model == "whisper-1"
    assert result.chunks == []
    assert cleanup_calls == [["/tmp/upload.wav", "/tmp/normalized.mp3"]]


def test_transcribe_file_transcribes_chunks_and_merges(monkeypatch):
    cleanup_calls = []
    chunks = [
        AudioChunk(index=1, path="/tmp/chunk1.mp3", start_seconds=1.0, end_seconds=2.0, size_bytes=10),
        AudioChunk(index=0, path="/tmp/chunk0.mp3", start_seconds=0.0, end_seconds=1.0, size_bytes=10),
    ]

    monkeypatch.setattr(
        transcription_service,
        "prepare_audio",
        lambda path: {
            "extracted_path": "/tmp/extracted.wav",
            "normalized_path": "/tmp/normalized.mp3",
            "size_bytes": 100,
        },
    )
    monkeypatch.setattr(transcription_service, "needs_chunking", lambda size: True)
    monkeypatch.setattr(transcription_service, "create_chunks", lambda path: chunks)
    monkeypatch.setattr(
        transcription_service,
        "transcribe_audio",
        lambda path: "後半" if path.endswith("chunk1.mp3") else "前半",
    )
    monkeypatch.setattr(transcription_service, "cleanup_temp_files", lambda paths: cleanup_calls.append(paths))

    result = transcription_service.transcribe_file("/tmp/upload.mp4")

    assert result.text == "前半 後半"
    assert result.duration_seconds == 2.0
    assert [chunk.index for chunk in result.chunks] == [0, 1]
    assert [chunk.text for chunk in result.chunks] == ["前半", "後半"]
    assert cleanup_calls == [
        [
            "/tmp/upload.mp4",
            "/tmp/normalized.mp3",
            "/tmp/extracted.wav",
            "/tmp/chunk1.mp3",
            "/tmp/chunk0.mp3",
        ]
    ]
