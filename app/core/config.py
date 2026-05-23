from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_transcription_model: str = "whisper-1"

    openai_max_upload_bytes: int = 25 * 1024 * 1024
    chunk_target_bytes: int = 20 * 1024 * 1024
    chunk_max_bytes: int = 23 * 1024 * 1024

    chunk_min_silence_len_ms: int = 700
    chunk_silence_thresh_db_offset: int = 16
    chunk_keep_silence_ms: int = 300

    chunk_fallback_min_silence_len_ms: int = 400
    chunk_fallback_silence_thresh_db_offset: int = 20
    chunk_time_fallback_overlap_seconds: float = 0.0

    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), str(BASE_DIR / ".env.local")),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
