from fastapi import FastAPI
from api.routers import transcription



app = FastAPI()

@app.get("/health")
def health_check():
  return {"status": "ok"}

app.include_router(transcription.router,  prefix="/api")