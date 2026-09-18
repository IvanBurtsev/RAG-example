"""Работа с векторной базой ChromaDB: индексация PDF и получение retriever'а."""
from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import settings
from .providers import get_embeddings


def get_vectorstore() -> Chroma:
    settings.ensure_dirs()
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )


def get_retriever() -> VectorStoreRetriever:
    return get_vectorstore().as_retriever(search_kwargs={"k": settings.retriever_k})


def _load_pdf(path: Path) -> list[Document]:
    docs = PyPDFLoader(str(path)).load()
    for doc in docs:
        doc.metadata["source"] = str(path.resolve())
        doc.metadata["file_name"] = path.name
    return docs


def ingest_data_dir() -> dict:
    """Индексирует все PDF из data/. Возвращает статистику по каждому файлу."""
    settings.ensure_dirs()
    pdfs = sorted(settings.data_dir.glob("*.pdf"))
    if not pdfs:
        return {"files": [], "chunks": 0, "message": f"В папке {settings.data_dir} нет PDF-файлов."}

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    store = get_vectorstore()

    stats: list[dict] = []
    total_chunks = 0
    for pdf in pdfs:
        source = str(pdf.resolve())
        pages = _load_pdf(pdf)
        chunks = splitter.split_documents(pages)
        if not chunks:
            stats.append({"file": pdf.name, "pages": len(pages), "chunks": 0})
            continue

        for chunk in chunks:
            chunk.metadata["source"] = source

        # переиндексация: удаляем прежние чанки этого файла
        try:
            store.delete(where={"source": source})
        except Exception:
            pass

        ids = [f"{pdf.stem}-{i}" for i in range(len(chunks))]
        store.add_documents(documents=chunks, ids=ids)

        total_chunks += len(chunks)
        stats.append({"file": pdf.name, "pages": len(pages), "chunks": len(chunks)})

    return {"files": stats, "chunks": total_chunks, "message": "Индексация завершена."}


def collection_stats() -> dict:
    store = get_vectorstore()
    count = store._collection.count()
    sources = store.get(include=["metadatas"]).get("metadatas", []) or []
    unique = sorted({m.get("file_name") for m in sources if m and m.get("file_name")})
    return {"chunks": count, "files": unique}
