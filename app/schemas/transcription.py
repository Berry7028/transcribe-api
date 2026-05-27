from pydantic import BaseModel, ConfigDict, Field


class TranscriptionChunk(BaseModel):
    """チャンク分割された場合に返す、音声内の範囲付き文字起こし結果。"""

    index: int
    start_seconds: float
    end_seconds: float
    text: str


class TranscriptionResponse(BaseModel):
    """文字起こしAPIの成功レスポンス。"""

    text: str
    language: str | None = None
    duration_seconds: float | None = None
    model: str
    chunks: list[TranscriptionChunk] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
