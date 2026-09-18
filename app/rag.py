"""RAG-цепочка: поиск релевантных чанков и генерация ответа LLM."""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .config import settings
from .ingest import get_vectorstore
from .providers import get_llm

SYSTEM_PROMPT = (
    "Ты — ассистент, который отвечает на вопросы строго по предоставленному контексту "
    "из PDF-документов. Если в контексте нет ответа, честно скажи об этом и не выдумывай. "
    "Отвечай на языке вопроса, структурированно и по делу."
)

USER_PROMPT = """Контекст:
{context}

Вопрос: {question}

Ответ:"""

_prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", USER_PROMPT)]
)


def format_docs(docs: list[Document]) -> str:
    if not docs:
        return "(контекст не найден)"
    blocks = []
    for doc in docs:
        name = doc.metadata.get("file_name", "документ")
        page = doc.metadata.get("page")
        page_part = f", стр. {page + 1}" if isinstance(page, int) else ""
        blocks.append(f"[{name}{page_part}]\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(blocks)


def _sources(docs: list[Document]) -> list[dict]:
    seen: set[tuple] = set()
    result: list[dict] = []
    for doc in docs:
        page = doc.metadata.get("page")
        page_number = page + 1 if isinstance(page, int) else None
        key = (doc.metadata.get("file_name"), page_number)
        if key in seen:
            continue
        seen.add(key)
        result.append(
            {
                "file": doc.metadata.get("file_name"),
                "page": page_number,
                "preview": doc.page_content.strip()[:300],
            }
        )
    return result


def answer_question(question: str) -> dict:
    retriever = get_vectorstore().as_retriever(search_kwargs={"k": settings.retriever_k})
    docs = retriever.invoke(question)

    chain = _prompt | get_llm() | StrOutputParser()
    text = chain.invoke({"context": format_docs(docs), "question": question})

    return {"answer": text, "sources": _sources(docs)}
