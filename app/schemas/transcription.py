from pydantic import BaseModel, ConfigDict, Field


class TranscriptionChunk(BaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    text: str


class TranscriptionResponse(BaseModel):
    text: str
    language: str | None = None
    duration_seconds: float | None = None
    model: str
    chunks: list[TranscriptionChunk] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
