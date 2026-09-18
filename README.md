# RAG PDF Assistant

RAG-ассистент на Python: загружает PDF, разбивает на чанки, сохраняет эмбеддинги в
ChromaDB и отвечает на вопросы по содержимому документов через FastAPI-веб-интерфейс.

## Возможности

- Загрузка PDF из папки `data/` или через веб-интерфейс.
- Разбиение документов на чанки (`RecursiveCharacterTextSplitter`) и индексация в ChromaDB.
- Поиск релевантных фрагментов и генерация ответа LLM (LangChain).
- Веб-интерфейс на FastAPI + простой REST API.
- Поддержка OpenAI-совместимых API и локального [Ollama](https://ollama.com/).

## Описание:
 RAG-ассистент для поиска ответов по PDF-документам с использованием LangChain, ChromaDB и FastAPI.

Стек: Python, FastAPI, LangChain, ChromaDB, DeepSeek V4 Flash, NeuroAPI.

## Структура проекта

```
.
├── app/
│   ├── __init__.py
│   ├── config.py        # настройки из .env
│   ├── providers.py     # фабрики embeddings и LLM
│   ├── ingest.py        # загрузка PDF, чанкинг, ChromaDB
│   ├── rag.py           # RAG-цепочка (retriever + LLM)
│   ├── main.py          # FastAPI-приложение
│   └── static/
│       └── index.html   # веб-интерфейс
├── data/                # сюда кладутся PDF
├── requirements.txt
├── .env.example
└── README.md
```

## Установка

```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Настройка

```bash
cp .env.example .env
```

Откройте `.env` и укажите `OPENAI_API_KEY`. Для OpenAI-совместимого сервиса задайте
`OPENAI_BASE_URL`.

### Вариант с локальной Ollama (без OpenAI)

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

В `.env`:

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
```

## Запуск

1. Положите PDF-файлы в папку `data/` (или загрузите их через веб-интерфейс).
2. Запустите сервер:

```bash
uvicorn app.main:app --reload
```

3. Откройте <http://127.0.0.1:8000> в браузере.

При старте PDF из `data/` индексируются автоматически (если `INGEST_ON_STARTUP=true`).
Повторная индексация того же файла заменяет его старые чанки.

## REST API

| Метод | Путь           | Описание                                   |
|-------|----------------|--------------------------------------------|
| GET   | `/`            | Веб-интерфейс                              |
| GET   | `/api/health`  | Проверка работоспособности                 |
| GET   | `/api/stats`   | Количество чанков и список файлов          |
| POST  | `/api/ingest`  | Индексировать все PDF из `data/`           |
| POST  | `/api/upload`  | Загрузить PDF (multipart `file`) и индексировать |
| POST  | `/api/ask`     | Задать вопрос `{"question": "..."}`        |

Пример запроса:

```bash
curl -X POST http://127.0.0.1:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "О чём этот документ?"}'
```

Пример ответа:

```json
{
  "answer": "Этот документ описывает...",
  "sources": [
    {"file": "report.pdf", "page": 3, "preview": "..."}
  ]
}
```

## Основные параметры `.env`

| Переменная          | По умолчанию            | Описание                          |
|---------------------|-------------------------|-----------------------------------|
| `LLM_PROVIDER`      | `openai`                | `openai` или `ollama`             |
| `EMBEDDING_PROVIDER`| `openai`                | `openai` или `ollama`             |
| `LLM_MODEL`         | `gpt-4o-mini`           | Модель генерации                  |
| `EMBEDDING_MODEL`   | `text-embedding-3-small`| Модель эмбеддингов                |
| `CHUNK_SIZE`        | `1000`                  | Размер чанка                      |
| `CHUNK_OVERLAP`     | `150`                   | Перекрытие чанков                 |
| `RETRIEVER_K`       | `4`                     | Сколько фрагментов подавать в LLM |
| `INGEST_ON_STARTUP` | `true`                  | Индексировать `data/` при старте  |
