from app.core.config import settings
from app.schemas.transcription import TranscriptionChunk, TranscriptionResponse
from app.services.chunk_service import AudioChunk, create_chunks, needs_chunking
from app.services.media_service import get_duration_seconds, prepare_audio
from app.services.merge_service import ChunkTranscription, merge_chunk_transcriptions
from app.services.openai_service import transcribe_audio
from app.utils.file_utils import cleanup_temp_files
from app.utils.time_utils import round_seconds


def transcribe_file(file_path: str) -> TranscriptionResponse:
    """アップロード済みファイルを正規化し、必要なら分割して文字起こしする。"""

    cleanup_paths = [file_path]
    processing_error: BaseException | None = None

    try:
        # Whisper API に渡す前に、動画抽出と音声形式の正規化を済ませる。
        prepared = prepare_audio(file_path)
        normalized_path = str(prepared["normalized_path"])
        cleanup_paths.append(normalized_path)

        extracted_path = prepared.get("extracted_path")
        if extracted_path:
            cleanup_paths.append(str(extracted_path))

        size_bytes = int(prepared["size_bytes"])
        if needs_chunking(size_bytes):
            # OpenAI のアップロード上限を超える場合は、チャンク単位で転記してから結合する。
            chunks = create_chunks(normalized_path)
            cleanup_paths.extend(chunk.path for chunk in chunks)
            return _transcribe_chunks(chunks)

        text = transcribe_audio(normalized_path)
        return TranscriptionResponse(
            text=text,
            language=None,
            duration_seconds=round_seconds(get_duration_seconds(normalized_path)),
            model=settings.openai_transcription_model,
            chunks=[],
        )
    except BaseException as exc:
        processing_error = exc
        raise
    finally:
        try:
            # 変換中に失敗しても、作成済みの一時ファイルは可能な限り片付ける。
            cleanup_temp_files(cleanup_paths)
        except Exception:
            # 元の処理エラーがある場合は、クリーンアップ失敗で本来の原因を隠さない。
            if processing_error is None:
                raise


def _transcribe_chunks(chunks: list[AudioChunk]) -> TranscriptionResponse:
    """チャンクごとの文字起こし結果をAPIレスポンス用に統合する。"""

    chunk_transcriptions: list[ChunkTranscription] = []

    for chunk in chunks:
        text = transcribe_audio(chunk.path)
        chunk_transcriptions.append(
            ChunkTranscription(
                index=chunk.index,
                start_seconds=chunk.start_seconds,
                end_seconds=chunk.end_seconds,
                text=text,
            )
        )

    merged = merge_chunk_transcriptions(chunk_transcriptions)
    return TranscriptionResponse(
        text=merged.text,
        language=None,
        duration_seconds=round_seconds(merged.duration_seconds),
        model=settings.openai_transcription_model,
        chunks=[
            TranscriptionChunk(
                index=chunk.index,
                start_seconds=chunk.start_seconds,
                end_seconds=chunk.end_seconds,
                text=chunk.text,
            )
            for chunk in merged.chunks
        ],
    )
