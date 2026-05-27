class TranscribeAPIError(Exception):
    """APIレスポンスへそのまま変換できるアプリ共通の基底例外。"""

    def __init__(self, code: str, message: str, status_code: int = 500) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UnsupportedFileTypeError(TranscribeAPIError):
    def __init__(self, allowed_extensions: set[str]) -> None:
        extensions = ", ".join(sorted(allowed_extensions))
        super().__init__(
            "unsupported_file_type",
            f"対応していないファイル形式です。対応形式: {extensions}",
            status_code=400,
        )


class InvalidRequestError(TranscribeAPIError):
    def __init__(self, message: str = "リクエスト形式が不正です") -> None:
        super().__init__("invalid_request", message, status_code=400)


class FileTooLargeForLocalProcessingError(TranscribeAPIError):
    def __init__(self, message: str) -> None:
        super().__init__(
            "file_too_large_for_local_processing",
            message,
            status_code=413,
        )


class FFmpegNotAvailableError(TranscribeAPIError):
    def __init__(self, message: str = "ffmpeg が利用できません") -> None:
        super().__init__("media_conversion_failed", message)


class MediaConversionError(TranscribeAPIError):
    def __init__(self, message: str) -> None:
        super().__init__("media_conversion_failed", message)


class MissingAPIKeyError(TranscribeAPIError):
    def __init__(self, message: str = "OpenAI API キーが設定されていません") -> None:
        super().__init__("transcription_failed", message)


class OpenAIAPIError(TranscribeAPIError):
    def __init__(self, message: str) -> None:
        super().__init__("transcription_failed", message)


class ChunkingFailedError(TranscribeAPIError):
    def __init__(self, message: str) -> None:
        super().__init__("chunking_failed", message)


class TemporaryFileCleanupError(TranscribeAPIError):
    def __init__(self, message: str) -> None:
        super().__init__("temporary_file_cleanup_failed", message)
