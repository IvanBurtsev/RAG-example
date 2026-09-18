"""FastAPI-приложение: веб-интерфейс и REST API RAG-ассистента."""
from __future__ import annotations

import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .config import BASE_DIR, settings
from .ingest import collection_stats, ingest_data_dir
from .rag import answer_question

STATIC_DIR = BASE_DIR / "app" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    if settings.ingest_on_startup:
        pdfs = list(settings.data_dir.glob("*.pdf"))
        if pdfs:
            try:
                ingest_data_dir()
            except Exception as exc:  # не роняем сервис из-за индексации
                print(f"[startup] Индексация не выполнена: {exc}")
    yield


app = FastAPI(title="RAG PDF Assistant", version="1.0.0", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Вопрос по содержимому PDF")


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/stats")
async def stats() -> dict:
    return collection_stats()


@app.post("/api/ingest")
async def ingest() -> dict:
    try:
        return ingest_data_dir()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Ожидается PDF-файл.")

    settings.ensure_dirs()
    target = settings.data_dir / Path(file.filename).name
    with target.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = ingest_data_dir()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"uploaded": target.name, **result}


@app.post("/api/ask", response_model=AskResponse)
async def ask(payload: AskRequest) -> AskResponse:
    try:
        return AskResponse(**answer_question(payload.question))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
