# Changelogs

## [Unreleased]

## [2026-03-07] - 260307-000006 - Metadata Extraction (Module 5)

### Added
- `supabase/migrations/20260307122049_add_document_metadata.sql` — Columns for title, summary, topics, document_type, language
- `supabase/migrations/20260307122204_search_chunks_with_metadata.sql` — Replaced search function to support metadata filtering
- `server/metadata.py` — Added Gemini API structured extraction using `DocumentMetadata`
- `test_mcp_metadata.py` — Smoke test for extraction and filtered search

### Changed
- `server/schemas.py` — Added `DocumentMetadata`
- `server/main.py` — Updated `search_documents` with optional type/topic filters, and `ingest_file` to populate metadata

## [2026-03-07] - 260307-000005 - Record Manager (Module 4)

### Added
- `supabase/migrations/20260307041258_add_content_hash_index.sql` — index on `documents(content_hash)` for fast dedup lookups
- `test_module4.py` — end-to-end smoke test for deduplication and re-ingestion

### Changed
- `server/main.py` `ingest_file` — added `force: bool = False` parameter; skips ingestion if same filename + same hash; deletes old doc and re-ingests if same filename + different hash
- `README.md` — updated tech stack (Gemini API), module list (9 modules, MCP-first), and added Testing section

## [2026-03-07] - 260307-000004 - Retrieval Tool (Module 3)

### Added
- `supabase/migrations/20260307071551_search_chunks.sql` — pgvector semantic search function with similarity thresholds
- `search_documents` MCP tool in `server/main.py` utilizing the new RPC function and the `embed_text` handler

## [2026-03-07] - 260307-000011 - Ingestion Smoke Test (Module 2)

### Changed
- `server/main.py` — restored Module 2 `ingest_file`, `list_documents`, `delete_document` functions
- `server/embeddings.py` — updated to use `gemini-embedding-001` via `GEMINI_API_KEY` rather than OpenRouter
- `.env` & `.env.example` — added `GEMINI_API_KEY` placeholder
- Module 2 completely validated against local Supabase instance

## [2026-03-07] - Switch from OpenRouter to Gemini API

### Changed
- `server/embeddings.py` — rewritten to use `google-genai` SDK with `gemini-embedding-001` (was OpenRouter `qwen3-embedding-0.6b`)
- `.env.example` — replaced `OPENROUTER_*` keys with `GEMINI_API_KEY`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_EMBEDDING_DIMENSIONS`
- PRD.md, CLAUDE.md, PROGRESS.md — all references updated from OpenRouter to Gemini API (free tier)
- Backlog plans (module5, module9) — updated to reference Gemini API
- Embeddings now use task types: `RETRIEVAL_DOCUMENT` for ingestion, `RETRIEVAL_QUERY` for search

### Added
- `google-genai` SDK dependency in `server/requirements.txt`

## [2026-03-07] - 260307-000003 - Document Ingestion via MCP (Module 2)

### Added
- `server/schemas.py` — Pydantic models for Document and Chunk
- `server/chunking.py` — recursive character text splitter (pure Python, no LangChain)
- `server/embeddings.py` — OpenRouter embedding API client (qwen3-embedding-0.6b, 768 dims, batch support)
- `ingest_file` MCP tool — read → chunk → embed → store in pgvector
- `list_documents` MCP tool — list all ingested documents
- `delete_document` MCP tool — cascade delete document + chunks + storage file
- `supabase/migrations/*_create_documents_table.sql` — documents table with RLS
- `supabase/migrations/*_create_chunks_table.sql` — chunks table with vector(768), ivfflat index, RLS
- `supabase/migrations/*_create_documents_storage_bucket.sql` — private documents storage bucket
- `test_data/sample.txt` — test file for smoke testing ingestion
- `.env.example` — added OPENROUTER_API_KEY, OPENROUTER_EMBEDDING_MODEL, OPENROUTER_EMBEDDING_DIMENSIONS

## [2026-03-07] - 260307-000002 - MCP Server Scaffold (Module 1)

### Added
- `server/main.py` — FastMCP server with stdio transport, `hello` and `supabase_health` tools
- `server/requirements.txt` — pinned dependencies (mcp, supabase, python-dotenv)
- `.mcp.json` — project-scoped MCP server registration for Claude Code
- `server/venv/` gitignored along with `__pycache__/` and `*.pyc`

### Changed
- `.gitignore` — added `server/venv/`, `__pycache__/`, `*.pyc`
- PRD.md, CLAUDE.md, PROGRESS.md, workflow.md — restructured for MCP-first architecture (9 modules)

## [2026-03-07] - 260307-000001 - PRD MCP Restructure

### Changed
- PRD.md — rewritten with 9-module MCP-first architecture
- CLAUDE.md — updated stack, rules, and project description for MCP-first
- PROGRESS.md — restructured to 9 modules with updated checklists
- docs/workflow.md — module reference and rules updated for MCP-first

### Removed
- Old web-first Module 1 (app-shell) plan archived to `docs/03_archive/`

## [2026-03-06] - 260306-000002 - Supabase Local Setup

### Added
- Supabase CLI installed, `supabase/` initialized, local stack running
- `.env` populated with local Supabase credentials
- `.env.example` with SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_URL
- pgvector extension enabled via migration (`20260306155855_enable_pgvector.sql`)
