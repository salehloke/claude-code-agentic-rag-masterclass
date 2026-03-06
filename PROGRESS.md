# Progress

Track your progress through the masterclass. Update this file as you complete modules - Claude Code reads this to understand where you are in the project.

## Convention
- `[ ]` = Not started
- `[-]` = In progress
- `[x]` = Completed

---

## Modules

### Module 1: App Shell + Observability
- [ ] Supabase project setup + `.env` configuration
- [ ] Auth (Supabase Auth - login/signup)
- [ ] RLS policies on `threads`, `messages`, `documents` tables
- [ ] Chat UI (React + shadcn/ui, threaded view)
- [ ] OpenAI Responses API integration (managed threads + file_search)
- [ ] LangSmith tracing setup
- [ ] Smoke test: user can log in, start a thread, get a response

### Module 2: BYO Retrieval + Memory
> Prerequisite: Architectural decision — replace Responses API with Chat Completions API
- [ ] Remove Responses API code + related DB schema
- [ ] Ingestion UI (drag-and-drop file upload)
- [ ] Supabase Storage for raw files
- [ ] Pydantic schemas for `Document` and `Chunk`
- [ ] PGVector setup (vector extension, embedding dimensions 1536/3072)
- [ ] Chunking → embedding → pgvector pipeline
- [ ] Retrieval tool (vector similarity search)
- [ ] OpenRouter / Ollama / LM Studio integration (Chat Completions API)
- [ ] Chat history storage (stateless API — store and send full history)
- [ ] Supabase Realtime for ingestion status updates
- [ ] Smoke test: upload a file, ask a question, get a grounded response

### Module 3: Record Manager
- [ ] SHA-256 content hashing on ingest
- [ ] Deduplication: skip if hash already exists and unchanged
- [ ] Delete old chunks + re-embed on file modification (prevent orphan chunks)
- [ ] Smoke test: upload same file twice, verify no duplicate chunks

### Module 4: Metadata Extraction
- [ ] `DocumentMetadata` Pydantic schema (title, summary, topics, document_type, language)
- [ ] LLM structured extraction from first 8,000 characters of document
- [ ] Store metadata in DB alongside chunks
- [ ] Metadata-filtered retrieval (filter search space before semantic match)
- [ ] Smoke test: ingest a PDF, verify metadata extracted and filterable

### Module 5: Multi-Format Support
- [ ] Docling integration for document parsing
- [ ] Support: PDF, DOCX, HTML, Markdown
- [ ] Standard pipeline (fast, CPU-friendly)
- [ ] Cascade deletes (delete document → delete all chunks)
- [ ] Smoke test: ingest one file of each format successfully

### Module 6: Hybrid Search + Reranking
- [ ] BM25 keyword search implementation
- [ ] Hybrid search: combine semantic (vector) + keyword (BM25) results
- [ ] RRF (Reciprocal Rank Fusion) to normalize and merge scores
- [ ] Reranker integration (Cohere or local bge-reranker)
- [ ] Smoke test: query with a specific product code, verify keyword result surfaces

### Module 7: Agentic Tools
- [ ] Tavily web search tool (fallback when docs don't have the answer)
- [ ] Text-to-SQL tool setup
- [ ] Read-only Postgres user (`sql_reader`) with restricted permissions
- [ ] Isolated connection string (`SQL_READER_URL`) on transaction pooler port 6543
- [ ] Agent routing: choose between retrieval, SQL, or web search per query
- [ ] Smoke test: ask a factual question not in docs, verify web search fallback fires

### Module 8: Sub-Agents
- [ ] `analyze_document` tool that spawns a sub-agent
- [ ] Sub-agent loads full document context (up to 70k+ tokens) in isolation
- [ ] Sub-agent returns summarized insight to main agent
- [ ] UI: `<think>` tag rendering (thought bubbles component)
- [ ] UI: hide/show toggle for reasoning output
- [ ] UI: nested tool call indicators with status + completion checkmarks
- [ ] Smoke test: ask to "analyze [document]", verify sub-agent spawns and returns insight

---

## Git Tags (Milestone Reference)

| Tag | Milestone |
|:----|:----------|
| `v0.1` | Module 1 — App Shell |
| `v0.2` | Module 2 — BYO Retrieval |
| `v0.3` | Module 3 — Record Manager |
| `v0.4` | Module 4 — Metadata |
| `v0.5` | Module 5 — Multi-Format |
| `v0.6` | Module 6 — Hybrid Search |
| `v0.7` | Module 7 — Agentic Tools |
| `v0.8` | Module 8 — Sub-Agents (Alpha) |
