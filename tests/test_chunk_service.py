from pathlib import Path

from app.services import chunk_service
from app.services.chunk_service import AudioChunk


def test_needs_chunking_uses_openai_upload_limit(monkeypatch):
    monkeypatch.setattr(chunk_service.settings, "openai_max_upload_bytes", 100)

    assert chunk_service.needs_chunking(101) is True
    assert chunk_service.needs_chunking(100) is False


def test_create_chunks_splits_until_audio_end(monkeypatch, tmp_path):
    source = tmp_path / "source.mp3"
    source.write_bytes(b"audio")

    class FakeAudio:
        # AudioSegment の長さだけが必要なテストなので、最小限のスタブにする。
        def __len__(self):
            return 2000

    split_calls = []

    def fake_find_split_ms(_audio, start_ms, duration_ms, _bytes_per_ms):
        split_calls.append((start_ms, duration_ms))
        if start_ms == 0:
            return (1000, False)
        return (duration_ms, False)

    def fake_export_with_size_limit(_source_path, output_path, start_ms, end_ms):
        Path(output_path).write_bytes(b"chunk")
        return AudioChunk(
            index=999,
            path=str(output_path),
            start_seconds=start_ms / 1000,
            end_seconds=end_ms / 1000,
            size_bytes=5,
        )

    monkeypatch.setattr(chunk_service, "_ensure_ffmpeg_available", lambda: None)
    monkeypatch.setattr(chunk_service, "_get_file_size", lambda _path: 200)
    monkeypatch.setattr(chunk_service.settings, "openai_max_upload_bytes", 100)
    monkeypatch.setattr(chunk_service.AudioSegment, "from_file", lambda _path: FakeAudio())
    monkeypatch.setattr(chunk_service, "_find_split_ms", fake_find_split_ms)
    monkeypatch.setattr(chunk_service, "_export_with_size_limit", fake_export_with_size_limit)
    monkeypatch.setattr(chunk_service, "_tmp_dir", lambda _name: tmp_path)

    chunks = chunk_service.create_chunks(str(source))

    assert split_calls == [(0, 2000), (1000, 2000)]
    assert [chunk.index for chunk in chunks] == [0, 1]
    assert [(chunk.start_seconds, chunk.end_seconds) for chunk in chunks] == [
        (0.0, 1.0),
        (1.0, 2.0),
    ]
