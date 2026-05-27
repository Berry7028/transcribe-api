from openai import OpenAI, OpenAIError
from app.core.config import settings
from app.core.errors import MissingAPIKeyError, OpenAIAPIError


def transcribe_audio(file_path: str) -> str:
    """単一の音声ファイルをOpenAIの文字起こしAPIへ送信する。"""

    if not settings.openai_api_key:
        raise MissingAPIKeyError()

    # APIキーはリクエスト時に設定するため、テストでは settings を差し替えやすい。
    client = OpenAI(api_key=settings.openai_api_key)

    try:
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=settings.openai_transcription_model,
                file=audio_file,
            )
        return transcription.text
    except OpenAIError as exc:
        raise OpenAIAPIError(f"OpenAI API 呼び出しに失敗しました: {str(exc)}") from exc
