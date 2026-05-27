from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routers import transcription
from app.core.errors import TranscribeAPIError


app = FastAPI()


@app.exception_handler(TranscribeAPIError)
async def transcribe_api_error_handler(_request: Request, exc: TranscribeAPIError) -> JSONResponse:
    # アプリ独自例外は、フロントエンドが扱いやすい共通の error 形式にそろえる。
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    # FastAPI の詳細なバリデーション情報は返さず、外部APIとして安定した文言にする。
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "invalid_request", "message": "リクエスト形式が不正です"}},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    # 5xx の内部情報をレスポンスに漏らさないよう、サーバー側エラーは固定文言にする。
    message = exc.detail if isinstance(exc.detail, str) else "リクエスト形式が不正です"
    code = "invalid_request"
    if exc.status_code >= 500:
        code = "internal_server_error"
        message = "サーバー内部でエラーが発生しました"

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message}},
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(transcription.router, prefix="/api")
