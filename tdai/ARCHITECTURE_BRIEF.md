# tencentDB (tdai) Agent-Memory System — Ground-Truth Architecture Brief
*Compiled by Ollie from live inspection of the installed plugin, 2026-06-22.*

This brief is the SOURCE OF TRUTH for three deliverables Rick requested:
1. A 20-slide PowerPoint explaining the system.
2. A plan to scale to 1,000 simultaneously-connected agents with rapid memory aggregation.
3. A plan to replace the Chinese-origin code with US-built code.

Do NOT invent architecture. Everything below was read from the actual installed package.

## What it is
- npm package: `@tencentdb-agent-memory/memory-tencentdb@1.0.0`, MIT license, author "TencentDB Agent Memory Team".
- Self-description: "Four-layer local memory system plugin for OpenClaw — auto-captures, structures, and profiles conversational knowledge using local LLM + SQLite vector search (L0→L1→L2→L3 pipeline)."
- It is an OpenClaw plugin (also ships a Hermes plugin variant). Requires OpenClaw >= 2026.3.13, Node >= 22.16.0.
- README is bilingual, Chinese-dominant.

## The four-layer pipeline (L0→L1→L2→L3)
- **L0 — Conversation recording (对话录制):** auto-captures every turn's raw messages. Dual-write: IMemoryStore (SQLite or TCVDB) + JSONL daily shards in `conversations/`.
- **L1 — Memory extraction (记忆提取):** an LLM extracts structured memories from L0 conversations. Vector dedup + conflict detection. Written to `records/` JSONL + IMemoryStore. Types: persona / episodic / instruction.
- **L2 — Scene induction (场景归纳):** an LLM incrementally induces "Scene Blocks" (topic-clustered .md summaries with a heat/hotness score) from L1 memories. Stored as `scene_blocks/*.md`.
- **L3 — Persona (用户画像):** an LLM generates/updates a long-form user persona profile (`persona.md`) from the scene blocks.

## Runtime hooks
- **Auto-Recall:** on `before_prompt_build`, vector/hybrid-searches relevant memories + loads persona, injects into system context. REQUIRES `allowPromptInjection` not be false (v2026.4.5+ safety control; if false, recall silently fails).
- **Auto-Capture:** on conversation end, records L0 then a Pipeline Scheduler triggers L1→L2→L3 after N conversations / idle timeouts.

## Data directory layout (`~/.openclaw/memory-tdai/` on CherryRd)
- `conversations/` — L0 daily JSONL (one msg per line)
- `records/` — L1 daily JSONL (extracted memories)
- `scene_blocks/` — L2 scene block .md files (e.g. AI-Benchmark-Operations.md, Paper-Replication-Project.md, etc.)
- `vectors.db` — SQLite + vec0 vector DB (sqlite backend only) — currently ~46 MB
- `persona.md` — L3 persona (currently ~42 KB)
- `.metadata/manifest.json` + `checkpoint.json` — store binding, seed info, pipeline checkpoints
- `.backup/` — rolling backups of persona + scene_blocks

## Storage backends (pluggable via `storeBackend`)
- **`sqlite`** (default, fully local): SQLite + `sqlite-vec` (asg017/sqlite-vec 0.1.7-alpha.2) for vector search; local embedding via `node-llama-cpp` (GGUF models) OR an external embedding endpoint.
- **`tcvdb`** (Tencent Cloud Vector Database): remote VDB at a URL+apiKey, server-side embedding + hybridSearch. Optional Tencent COS object storage (`cos-nodejs-sdk-v5`).

## Search / retrieval
- Strategies: `hybrid` (keyword + vector via RRF fusion), pure `embedding`, keyword.
- BM25 sparse vectors via `@tencentdb-agent-memory/tcvdb-text` (built-in BM25 encoder, CN/EN mixed).
- Chinese tokenization via `@node-rs/jieba` (jieba segmenter, Rust binding).
- Agent-facing tools: `tdai_memory_search` (L1), `tdai_conversation_search` (L0), `tdai_read_cos` (read scene/persona files). Also a UMP-pilot MCP surface: `ump-recall`, `ump-get`, `ump-capabilities`.

## Key config knobs (`~/.openclaw/openclaw.json` → `memory-tencentdb`)
- capture: enabled, excludeAgents, l0l1RetentionDays(90), cleanTime
- extraction: enableDedup, maxMemoriesPerSession(20), model
- persona: triggerEveryN(50), maxScenes(15), backupCount
- pipeline: everyNConversations(5), l1IdleTimeoutSeconds(600), l2 intervals
- recall: maxResults(5), scoreThreshold(0.3), strategy(hybrid), timeoutMs(5000)
- embedding: provider, baseUrl, model(text-embedding-3-small), dimensions(1536)

## CHINESE-ORIGIN COMPONENTS (relevant to deliverable #3)
- Whole package authored by "TencentDB Agent Memory Team" (Tencent). README/CHANGELOG Chinese-dominant.
- `@tencentdb-agent-memory/memory-tencentdb` (the plugin)
- `@tencentdb-agent-memory/memory-sdk-ts` (SDK)
- `@tencentdb-agent-memory/tcvdb-text` (BM25 encoder)
- `@node-rs/jieba` (Chinese tokenizer, Rust)
- optional: `cos-nodejs-sdk-v5` (Tencent COS), TCVDB remote backend (Tencent Cloud)
- A notable behavior observed live: the recall pipeline's injected "relevant-memories" and persona blocks are often rendered in Chinese.

## US-buildable equivalents (for deliverable #3 — replacement targets)
- Plugin/pipeline: rewrite the L0→L3 orchestration as a clean-room US-authored OpenClaw plugin (TypeScript). The pipeline design is straightforward; the value is in prompts + scheduling.
- Vector store: keep `sqlite-vec` (asg017, US/OSS, public-domain-ish) OR move to pgvector (Postgres) / LanceDB / Qdrant (all OSS, non-Chinese) / Milvus-alt. For scale: pgvector or Qdrant.
- Embeddings: OpenAI text-embedding-3 / Voyage / Cohere / local US OSS (e.g. nomic-embed, BGE-from-HF run locally) — but choose US-origin (nomic-embed-text is US/Nomic AI).
- BM25/sparse: use Tantivy (Rust, US/OSS), or Elasticsearch/OpenSearch BM25, or a clean-room BM25.
- Tokenization: replace jieba with a US/OSS tokenizer; for EN-dominant use tiktoken (OpenAI) + ICU/unicode segmentation; for CN keep an OSS non-Tencent segmenter if needed.
- Object storage: S3 / MinIO instead of Tencent COS.
- Remote VDB: self-hosted Qdrant/pgvector/Milvus instead of TCVDB.

## Current live state (CherryRd)
- Backend in use: sqlite (local). vectors.db 46 MB, persona.md 42 KB, 6+ scene blocks.
- Both Ollie (CherryRd) and Kukla (m1) run this memory system.
