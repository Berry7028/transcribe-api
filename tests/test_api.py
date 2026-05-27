from fastapi.testclient import TestClient

from app.api.routers import transcription
from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_transcriptions_rejects_unsupported_file_type():
    response = client.post(
        "/api/transcriptions",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_file_type"


def test_transcriptions_uses_prepared_audio_and_returns_text(monkeypatch):
    monkeypatch.setattr(
        transcription,
        "prepare_audio",
        lambda path: {"normalized_path": "/tmp/normalized.mp3", "size_bytes": 42},
    )
    monkeypatch.setattr(transcription, "transcribe_audio", lambda path: "文字起こし結果")

    response = client.post(
        "/api/transcriptions",
        files={"file": ("voice.wav", b"fake audio", "audio/wav")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "voice.wav"
    assert body["normalized_path"] == "/tmp/normalized.mp3"
    assert body["size_bytes"] == 42
    assert body["text"] == "文字起こし結果"
