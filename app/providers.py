"""Фабрики моделей: эмбеддинги и LLM (OpenAI-совместимые или Ollama)."""
from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from .config import settings


def _require_openai_key() -> str:
    if not settings.openai_api_key:
        raise RuntimeError(
            "Не задан OPENAI_API_KEY. Скопируйте .env.example в .env и заполните ключ, "
            "либо переключите провайдера на ollama (LLM_PROVIDER=ollama, EMBEDDING_PROVIDER=ollama)."
        )
    return settings.openai_api_key


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    if settings.embedding_provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=_require_openai_key(),
        base_url=settings.openai_base_url,
    )


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            temperature=settings.temperature,
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=_require_openai_key(),
        base_url=settings.openai_base_url,
        temperature=settings.temperature,
    )
