from fastapi.testclient import TestClient

from app.api.routers import transcription
from app.main import app
from app.schemas.transcription import TranscriptionResponse


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


def test_transcriptions_uses_service_and_returns_transcription(monkeypatch):
    service_calls = []

    def fake_transcribe_file(path):
        # API層の責務だけを検証するため、実際のffmpeg/OpenAI呼び出しは避ける。
        service_calls.append(path)
        return TranscriptionResponse(
            text="文字起こし結果",
            language=None,
            duration_seconds=1.25,
            model="whisper-1",
            chunks=[],
        )

    monkeypatch.setattr(transcription, "transcribe_file", fake_transcribe_file)

    response = client.post(
        "/api/transcriptions",
        files={"file": ("voice.wav", b"fake audio", "audio/wav")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "文字起こし結果"
    assert body["duration_seconds"] == 1.25
    assert body["model"] == "whisper-1"
    assert body["chunks"] == []
    assert len(service_calls) == 1
    assert service_calls[0].endswith(".wav")
