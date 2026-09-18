# AGENTS.md

RAG PDF assistant: FastAPI + LangChain + ChromaDB. PDFs in `data/` are chunked,
embedded into a persistent Chroma store, and queried via a web UI / REST API.

## Setup and commands
- Install: `pip install -r requirements.txt` (no lockfile; this repo runs on Python 3.14).
- Configure: `cp .env.example .env`, then set `OPENAI_API_KEY` (or set both `LLM_PROVIDER=ollama` and `EMBEDDING_PROVIDER=ollama`).
- Run from the repo root: `uvicorn app.main:app --reload`. Relative imports require the repo root on `sys.path`.
- **No tests, linter, formatter, or typecheck config exists.** `test.py` is a scratch file, not a test. Verify changes manually by running the server and calling `/api/health`, `/api/stats`, `/api/ask`.

## Architecture
- `app/main.py` — FastAPI app. Lifespan auto-ingests `data/` when `INGEST_ON_STARTUP=true`; failures are logged and do not crash the server.
- `app/config.py` — frozen `Settings` singleton `settings`, loaded from the repo-root `.env` via python-dotenv. Paths resolve relative to `BASE_DIR` (repo root), not CWD.
- `app/providers.py` — `get_embeddings()` / `get_llm()` factories, `lru_cache`d. Provider chosen independently per capability via `LLM_PROVIDER` / `EMBEDDING_PROVIDER` (`openai` = any OpenAI-compatible API, or `ollama`).
- `app/ingest.py` — Chroma persists to `chroma_db/`. Re-ingesting a PDF deletes its old chunks by `source` metadata before adding new ones; chunk ids are `{stem}-{i}`.
- `app/rag.py` — retriever (`RETRIEVER_K`) + chat prompt; returns `{answer, sources}` with 1-based page numbers.

## Repo-specific gotchas
- Comments, docstrings, prompts, and all user-/LLM-facing strings are **Russian**. Keep new ones Russian.
- The live `.env` points at NeuroAPI (`OPENAI_BASE_URL=https://neuroapi.host/v1`, `LLM_MODEL=deepseek-v4-flash`), not OpenAI. The README defaults (`gpt-4o-mini`) are stale; trust `.env`.
- `.env`, `chroma_db/`, and `data/*.pdf` are gitignored. Never commit their contents.
- `.opencode/plugins/code-agent-auto-commit.ts` invokes the `cac` runner on every session-idle event for worktree `/mnt/c/AI`, which **auto-commits changes without an explicit request**. Expect commits to appear on their own.
