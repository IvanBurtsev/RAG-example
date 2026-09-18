"""Конфигурация приложения. Значения читаются из переменных окружения / .env."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(_env("DATA_DIR", str(BASE_DIR / "data"))))
    chroma_dir: Path = field(
        default_factory=lambda: Path(_env("CHROMA_DIR", str(BASE_DIR / "chroma_db")))
    )
    collection_name: str = field(default_factory=lambda: _env("COLLECTION_NAME", "pdf_documents"))

    chunk_size: int = field(default_factory=lambda: int(_env("CHUNK_SIZE", "1000")))
    chunk_overlap: int = field(default_factory=lambda: int(_env("CHUNK_OVERLAP", "150")))
    retriever_k: int = field(default_factory=lambda: int(_env("RETRIEVER_K", "4")))

    llm_provider: str = field(default_factory=lambda: (_env("LLM_PROVIDER", "openai") or "openai").lower())
    embedding_provider: str = field(
        default_factory=lambda: (_env("EMBEDDING_PROVIDER", "openai") or "openai").lower()
    )

    openai_api_key: str | None = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    openai_base_url: str | None = field(default_factory=lambda: _env("OPENAI_BASE_URL"))
    llm_model: str = field(default_factory=lambda: _env("LLM_MODEL", "gpt-4o-mini"))
    embedding_model: str = field(default_factory=lambda: _env("EMBEDDING_MODEL", "text-embedding-3-small"))
    temperature: float = field(default_factory=lambda: float(_env("TEMPERATURE", "0.0")))
    ingest_on_startup: bool = field(
        default_factory=lambda: (_env("INGEST_ON_STARTUP", "true") or "true").lower() in ("1", "true", "yes")
    )

    ollama_base_url: str = field(default_factory=lambda: _env("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_llm_model: str = field(default_factory=lambda: _env("OLLAMA_LLM_MODEL", "llama3.1"))
    ollama_embedding_model: str = field(
        default_factory=lambda: _env("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    )

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
