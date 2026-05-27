from app.services import media_service


def test_prepare_audio_extracts_video_before_normalizing(monkeypatch):
    calls = []

    monkeypatch.setattr(media_service, "ensure_ffmpeg_available", lambda: calls.append("ensure"))
    monkeypatch.setattr(
        media_service,
        "extract_audio",
        lambda path: calls.append(("extract", path)) or "/tmp/extracted.wav",
    )
    monkeypatch.setattr(
        media_service,
        "normalize_audio",
        lambda path: calls.append(("normalize", path)) or "/tmp/normalized.mp3",
    )
    monkeypatch.setattr(media_service, "get_file_size", lambda path: 1234)

    result = media_service.prepare_audio("/tmp/source.mp4")

    assert calls == [
        "ensure",
        ("extract", "/tmp/source.mp4"),
        ("normalize", "/tmp/extracted.wav"),
    ]
    assert result == {"normalized_path": "/tmp/normalized.mp3", "size_bytes": 1234}


def test_prepare_audio_normalizes_audio_without_extracting(monkeypatch):
    calls = []

    monkeypatch.setattr(media_service, "ensure_ffmpeg_available", lambda: calls.append("ensure"))
    monkeypatch.setattr(media_service, "extract_audio", lambda path: calls.append(("extract", path)))
    monkeypatch.setattr(
        media_service,
        "normalize_audio",
        lambda path: calls.append(("normalize", path)) or "/tmp/normalized.mp3",
    )
    monkeypatch.setattr(media_service, "get_file_size", lambda path: 5678)

    result = media_service.prepare_audio("/tmp/source.wav")

    assert calls == ["ensure", ("normalize", "/tmp/source.wav")]
    assert result["normalized_path"] == "/tmp/normalized.mp3"
    assert result["size_bytes"] == 5678
