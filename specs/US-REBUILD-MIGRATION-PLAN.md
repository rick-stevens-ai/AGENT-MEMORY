# Replacing the Chinese-Origin Memory Code with US-Built Code
### A clean-room repatriation plan for the tdai agent-memory system
*Author: Ollie (Rick Stevens / Argonne) — 2026-06-22. Grounded in live inspection of the installed `@tencentdb-agent-memory/memory-tencentdb` v1.0.0 plugin and its dependency manifest.*

---

## 0. TL;DR
Good news: the package is **MIT-licensed** and its **core (the L0→L1→L2→L3 pipeline, SQLite+FTS5+sqlite-vec storage, ai-sdk LLM calls running locally on `argo:claude-sonnet-4.6`) is already vendor-neutral and runs fully on-prem.** The genuinely **China-origin / Tencent-coupled surface is narrow**: the BM25 text encoder (`@tencentdb-agent-memory/tcvdb-text`), the Tencent SDK (`@tencentdb-agent-memory/memory-sdk-ts`), the optional Tencent Cloud Object Storage client (`cos-nodejs-sdk-v5`), the optional Tencent Cloud Vector DB (TCVDB) backend + its migration tools, and the Chinese tokenizer (`@node-rs/jieba`, China-origin OSS, not Tencent). The right move is a **clean-room US-authored TypeScript rewrite of the orchestration** plus **drop-in US/US-OSS replacements** for each coupled component, with a **compatibility shim** so the `tdai_*` tools keep working through a dual-run cutover. No data loss; full provenance/data-residency control.

---

## 0.5 Independent cross-validation (two-agent convergence)
This inventory was produced **independently on two hosts** and converged:
- **Ollie / CherryRd** (this plan): inspected the installed plugin + npm manifest + data dir.
- **Kukla / m1**: inspected `~/.memory-tencentdb/tdai-memory-openclaw-plugin/` source tree.

Both arrived at the same narrow China-coupling surface: **MIT-licensed, fully local core**, with coupling limited to 2 Tencent npm packages (`tcvdb-text`, `memory-sdk-ts`) + the (off-by-default) Tencent COS SDK + ~6 files under `src/core/store/` + the `jieba` (China-origin OSS) tokenizer. Independent agreement raises confidence that the repatriation is small and well-bounded.

**Config-divergence reconcile (resolved):** the two live instances differ — Kukla's m1 runs `embedding=DISABLED` (lexical/BM25-only) while Ollie's CherryRd runs `embedding=ENABLED` via `argo:text-embedding-3-small`. **Resolution: standardize the US build on Argo-served embeddings** (`text-embedding-3-small` through the on-prem Argo proxy) — never a China concern, on-prem, free, and gives semantic recall on every instance. The CherryRd (embeddings-enabled) config is treated as canonical.

## 1. Why repatriate (rationale)
- **Provenance / supply chain:** a memory subsystem sees *everything* an agent thinks. Authorship and dependency origin matter for trust.
- **Data residency:** the optional TCVDB + COS backends would egress agent memory to Tencent Cloud. Even unused, the code paths exist. Remove them.
- **Auditability:** a US clean-room build lets us own the prompts, schema, and retention logic outright.
- **Language artifacts:** recall output and persona blocks currently render heavily in Chinese (jieba + zh BM25 + Chinese prompt scaffolding). US rebuild standardizes on English-first tokenization/segmentation.

---

## 2. Component inventory (what is China-origin vs vendor-neutral)

| Component | Origin | Coupling | Action |
|---|---|---|---|
| `@tencentdb-agent-memory/memory-tencentdb` (plugin core) | Tencent (MIT) | The orchestration itself | **Clean-room rewrite** (US-authored TS) |
| `@tencentdb-agent-memory/memory-sdk-ts` | Tencent | SDK glue | Replace with native US-authored store/client code |
| `@tencentdb-agent-memory/tcvdb-text` (BM25) | Tencent | Sparse/BM25 encoding | Replace with **Tantivy** (Rust/US OSS) or OpenSearch BM25, or clean-room BM25 |
| `cos-nodejs-sdk-v5` (Tencent COS) | Tencent | Object storage (optional) | Replace with **AWS S3 SDK / MinIO** |
| TCVDB remote backend + `migrate-sqlite-to-tcvdb`, `export-tencent-vdb` | Tencent Cloud | Remote VDB (optional) | **Remove**; replace with self-hosted **Qdrant / pgvector** |
| `@node-rs/jieba` (segmenter) | China OSS (not Tencent) | Chinese tokenization | Replace with **ICU/Unicode segmentation + tiktoken** (EN-first); optional non-Tencent CN segmenter only if CN needed |
| `sqlite-vec` (asg017) | US OSS | Vector search | **Keep** (US-origin, OSS) |
| `ai` / `@ai-sdk/openai` (Vercel) | US OSS | LLM calls | **Keep** |
| `js-tiktoken`, `dayjs`, `zod`, `undici`, `crc-32`, `json5`, `yaml` | US/neutral OSS | utilities | Keep |
| OpenTelemetry stack | CNCF/neutral | observability | Keep |

**Net:** only ~5 items are China-origin and must be replaced; 2 are optional cloud hooks we simply delete; the bulk is already keep-able US/neutral OSS.

---

## 3. US replacement mapping (component-by-component)
- **Vector store:** `sqlite-vec` (local, keep) → for scale, **pgvector** (PostgreSQL, US/OSS) or **Qdrant** (Rust, OSS). Both non-Chinese, self-hostable, no cloud egress.
- **Sparse/BM25:** `tcvdb-text` → **Tantivy** (Rust full-text/BM25, US-led OSS) or **OpenSearch** (US/Amazon fork) BM25; or a small clean-room BM25 over SQLite FTS5 (already present) for English.
- **Tokenizer/segmentation:** `@node-rs/jieba` → **tiktoken** (OpenAI, US) for token accounting + **ICU word segmentation / Intl.Segmenter** (Unicode, neutral) for indexing. Drop the zh-default; English-first.
- **Object storage:** `cos-nodejs-sdk-v5` → **@aws-sdk/client-s3** against AWS S3 or self-hosted **MinIO** (Apache-2.0).
- **Remote VDB backend:** TCVDB → self-hosted Qdrant/pgvector; delete the Tencent migration/export tools.
- **Embeddings:** keep provider-agnostic ai-sdk; default to **OpenAI text-embedding-3** or **Nomic embed (Nomic AI, US)** or local US OSS (BGE run on our GPUs). No change needed — already pluggable.
- **LLM extraction:** already `argo:claude-sonnet-4.6` via Argo proxy (on-prem, free). Keep.

---

## 4. Clean-room rewrite strategy (avoid copying)
- **Re-implement from spec, not source.** Document the L0→L3 contract (record schemas, pipeline cadence, recall hook behavior) as a US-authored spec, then implement fresh TypeScript against it. We already have the spec ground-truth from inspection (record types, FTS5 schema v2, scheduler cadence: every-5-conversations L1, 600s L1 idle, L2 +10s/900–3600s, 24h session window).
- **Reuse only the public OpenClaw plugin SDK contracts** (`before_prompt_build` hook, tool registration) — those are OpenClaw's, not Tencent's.
- **Keep the proven OSS libraries** (sqlite-vec, ai-sdk, zod, OTel) — using an OSS dependency is not "copying Chinese code."
- **Prompts:** rewrite the L1/L2/L3 extraction/synthesis prompts in English, US-authored, tuned on our data.
- New package name + US authorship + clear LICENSE/PROVENANCE.

---

## 5. Data migration path (no loss)
Current data on disk: `vectors.db` (SQLite + FTS5 + optional vec0), `conversations/` (L0 JSONL), `records/` (L1 JSONL), `scene_blocks/*.md` (L2), `persona.md` (L3), `.metadata/manifest.json`.
- **Step 1:** Export from SQLite/JSONL via a US-authored exporter (not the Tencent `export-tencent-vdb` tool) → portable JSON/Parquet with full provenance.
- **Step 2:** Re-embed (if switching embedding models) on our GPUs, or carry vectors forward if dimensions match.
- **Step 3:** Bulk-load into the new store (pgvector/Qdrant) preserving record IDs, timestamps, tier, agent namespace.
- **Step 4:** Checksum/row-count parity check old vs new; spot-check recall results match (top-k overlap ≥ threshold) before cutover.
- L2 scene_blocks and L3 persona are plain markdown — copy verbatim, no transformation needed.

---

## 6. Compatibility shim (zero-downtime cutover)
- Keep the **same agent-facing tool names** (`tdai_memory_search`, `tdai_conversation_search`, `tdai_read_cos`, plus UMP `ump-recall`/`ump-get`) so no prompt or agent behavior changes.
- The new US plugin registers those identical tool IDs; internally they hit the new store.
- **Dual-run window:** run old (read-only) + new (read-write) simultaneously; route reads to new, compare against old, until parity confirmed; then disable old.

---

## 7. Security / supply-chain outcomes
- Zero Tencent Cloud egress paths in the codebase (TCVDB + COS removed, not just disabled).
- All dependencies US/neutral-OSS with pinned, audited versions; SBOM generated.
- Memory data stays on Argonne/CELS infra end-to-end.
- US-authored prompts, schema, retention, and orchestration — full ownership.

---

## 8. Phased migration
- **Phase A (1 wk):** Write the US-authored spec + exporter; stand up pgvector/Qdrant + MinIO/S3; SBOM the current deps.
- **Phase B (2–3 wk):** Clean-room implement the L0→L3 plugin in TS against the spec; swap BM25→Tantivy/OpenSearch, jieba→ICU/tiktoken, COS→S3/MinIO; keep sqlite-vec/ai-sdk.
- **Phase C (1 wk):** Migrate one agent's data (Ollie or a test instance), dual-run, verify recall parity.
- **Phase D (1–2 wk):** Roll to all agents; remove Tencent packages from the dependency tree; decommission old plugin; ship PROVENANCE + LICENSE.

---

## 9. Effort & risk
- **Effort:** ~5–7 focused weeks for a clean-room rewrite + migration of current instances (the design is well-understood; most risk is in prompt-tuning parity and search-quality parity, not infrastructure).
- **Risks:**
  - *Search-quality regression* swapping BM25/tokenizer — mitigate with side-by-side recall eval (top-k overlap, multi-judge relevance per Rick's scoring rule) before cutover.
  - *Embedding dimension mismatch* if changing models — re-embed on our GPUs, cheap.
  - *Hidden Tencent coupling* in transitive deps — SBOM audit catches it.
  - *Behavioral drift* in extraction — freeze the spec, A/B the new prompts against logged conversations.
- **Leverage:** the MIT license + already-local core means this is a *repatriation + hardening*, not a from-zero build.
