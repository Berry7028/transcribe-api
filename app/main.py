from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers import transcription
from core.errors import TranscribeAPIError


app = FastAPI()


@app.exception_handler(TranscribeAPIError)
async def transcribe_api_error_handler(_request: Request, exc: TranscribeAPIError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": {"code": exc.code, "message": exc.message}},
    )

@app.get("/health")
def health_check():
  return {"status": "ok"}

app.include_router(transcription.router,  prefix="/api")