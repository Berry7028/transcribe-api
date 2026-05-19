class TranscribeAPIError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class FFmpegNotAvailableError(TranscribeAPIError):
    def __init__(self, message: str = "ffmpeg が利用できません") -> None:
        super().__init__("media_conversion_failed", message)


class MediaConversionError(TranscribeAPIError):
    def __init__(self, message: str) -> None:
        super().__init__("media_conversion_failed", message)
