# System Specification — tdai Swarm Memory Platform (1,000 Agents)
### Buildable engineering spec for a multi-tenant agent-memory service
*Author: Ollie (Rick Stevens / Argonne) — 2026-06-22. Companion to SCALE-1000-AGENTS-PLAN.md (strategy) and US-REBUILD-MIGRATION-PLAN.md (provenance). This document is the implementation spec: components, interfaces, schemas, APIs, sizing, SLOs.*

---

## 1. Scope & goals
Build a memory platform that hosts **1,000 concurrently-connected agents**, each with private long-term memory (L0→L1→L2→L3), plus a shared **swarm memory** tier that rapidly aggregates knowledge across agents. Preserve the existing tdai tool contract (`tdai_memory_search`, `tdai_conversation_search`, `tdai_read_cos`, UMP). US-OSS components only (per repatriation plan).

**Non-goals:** replacing the agent runtime (OpenClaw/Hermes); changing the agent-facing tool names; cloud-vendor lock-in.

---

## 2. System context (C4 level-1)
```
[ 1,000 Agents ] --tools/gRPC/HTTP--> [ tdai Memory Service ] --> [ Shared Store + Bus + Workers ]
                                              │
                                       [ Swarm Aggregator ]
```
Actors: agent runtimes (clients), operators (ops/observability), the aggregation service (internal).

---

## 3. Component inventory & responsibilities

| # | Component | Tech (US-OSS) | Responsibility | Scaling |
|---|---|---|---|---|
| C1 | **Memory API Gateway** | TypeScript/Node (Hono) or Go | Auth, tenancy resolution, tool endpoints (recall/capture/search), rate limit | Stateless, N replicas behind LB |
| C2 | **Ingestion Bus** | NATS JetStream (preferred) or Kafka | Durable L0 capture stream, partitioned by `agent_id` | Cluster, 3+ nodes |
| C3 | **Extraction Worker Pool** | Node/TS workers + ai-sdk | Consume bus → L1→L2→L3 (idempotent) | Horizontal, autoscale on lag |
| C4 | **Shared Memory Store** | Qdrant (vec) **or** Postgres+pgvector | Multi-tenant vector+payload store; private & swarm tiers | Sharded by `agent_id` hash, replicated |
| C5 | **Lexical/BM25 Index** | OpenSearch **or** Tantivy | Sparse/keyword retrieval for hybrid search | Sharded with C4 |
| C6 | **Embedding Service** | ai-sdk → Argo `text-embedding-3-small` | Batched embeddings (1536-dim) | Batch queue; GPU-backed if local model |
| C7 | **Swarm Aggregator** | Node/TS service | Cross-agent dedup, conflict-resolve (multi-judge), rollup | Scheduled + event-driven |
| C8 | **Recall Cache** | Redis | Cache recall results keyed (agent_id, query-bucket) | Cluster |
| C9 | **Object Storage** | S3 or MinIO | Large artifacts, backups, JSONL archive | Native |
| C10 | **Observability** | OpenTelemetry → Prometheus/Grafana/Tempo | Traces, metrics, logs, SLO dashboards | Native |
| C11 | **Control Plane** | Postgres (metadata) | Tenant registry, quotas, pipeline checkpoints, manifests | HA pair |

---

## 4. Data model & schemas

### 4.1 Tenancy
- `tenant` = one agent. Key: `agent_id` (string). All records carry `agent_id` + `tier ∈ {private, swarm}`.
- Namespacing: Qdrant payload-index on `agent_id`; or pgvector partition by `agent_id` hash (e.g. 64 partitions).

### 4.2 Record schemas (canonical, store-agnostic)
**L0 conversation message**
```json
{ "id":"uuid", "agent_id":"str", "session_id":"str", "ts":"iso8601",
  "role":"user|assistant|system|tool", "text":"str",
  "hash":"sha256(text+session+ts)",  // idempotency key
  "tier":"private" }
```
**L1 memory**
```json
{ "id":"uuid", "agent_id":"str", "type":"persona|episodic|instruction",
  "text":"str", "embedding":[float;1536]?, "ts":"iso8601",
  "source_l0":["uuid"], "dedup_hash":"simhash", "confidence":0.0-1.0,
  "conflict_state":"none|disputed", "tier":"private|swarm",
  "provenance":{"seen_by":["agent_id"],"created_by":"agent_id"} }
```
**L2 scene block**
```json
{ "id":"uuid", "agent_id|swarm":"str", "topic":"str", "summary_md":"str",
  "heat":int, "member_l1":["uuid"], "updated":"iso8601", "tier":"private|swarm" }
```
**L3 persona**
```json
{ "agent_id|swarm":"str", "persona_md":"str", "version":int,
  "updated":"iso8601", "source_scenes":["uuid"] }
```

### 4.3 Indexes
- Vector: HNSW on `embedding` (cosine), per shard.
- Lexical: BM25 over `text` (L0+L1).
- Payload: `agent_id`, `tier`, `type`, `ts`, `topic`.

---

## 5. Service APIs (the contract)

### 5.1 Agent-facing (preserve tdai tool names)
- `POST /v1/capture` — body: L0 message(s). Returns `202` (async via bus). Idempotent on `hash`.
- `POST /v1/recall` — body `{agent_id, query, k, strategy, include_swarm:bool}`. Returns ranked memories (private ∪ swarm), RRF-fused. SLO p95 ≤ 150 ms.
- `POST /v1/memory_search` (→ `tdai_memory_search`) — L1 semantic/hybrid search.
- `POST /v1/conversation_search` (→ `tdai_conversation_search`) — L0 search.
- `GET /v1/read?path=` (→ `tdai_read_cos`) — scene/persona fetch.
- UMP: `ump-recall`, `ump-get`, `ump-capabilities` (compat surface).

### 5.2 Internal
- Bus topics: `mem.l0.capture` (partitioned by agent_id), `mem.l1.ready`, `mem.l2.ready`.
- Aggregator: `POST /internal/aggregate {topic|agent_ids}`; emits swarm records.
- Embedding: `POST /internal/embed {texts[]}` → vectors (batched).

### 5.3 Auth
- mTLS or signed service tokens between agents and gateway; per-tenant API key; ACL: an agent may read its own `private` + the `swarm` tier, never another agent's `private`.

---

## 6. Pipeline behavior (preserve current semantics, distribute execution)
- L0 capture → bus (immediate, durable).
- L1: trigger every 5 conversations OR 600 s idle; worker extracts, dedups (simhash + embedding sim), conflict-checks, writes.
- L2: ~10 s after L1, interval 900–3600 s; induce/update scene blocks.
- L3: persona regenerate every N (≈50); rolling backups.
- Swarm: aggregator runs on cadence (e.g. every 50 new private L1 per topic) → dedup/conflict/rollup → swarm tier.
- All stages **idempotent** (hash/id keyed upserts) so at-least-once bus delivery is safe.

---

## 7. Capacity & resource sizing (1,000 agents)
ASSUMPTIONS (tune with telemetry): 200 turns/agent/day; L1 every 5 conv; ~3 memories/extraction.
- L0: ~200k msgs/day (~2.3/s avg, ~25/s burst).
- L1: ~40k extractions/day (~0.5/s); ~120k memory records/day.
- Embeddings: ~120k/day (~1.4/s) — batchable; 1 A100 OSS embedder >10k/s → trivial headroom.
- Storage: ~120k×~6 KB ≈ ~700 MB/day raw (with vectors) → ~250 GB/yr pre-dedup; swarm dedup reduces.
- Recall QPS: 1,000 agents × ~1 recall/turn at active concurrency → design for ~200–500 recall QPS peak.

**Sizing (starting point):**
- C1 Gateway: 3× (4 vCPU / 8 GB).
- C2 Bus: 3× NATS (4 vCPU / 16 GB / fast disk).
- C3 Workers: 10× (8 vCPU / 16 GB), autoscale to 30 on lag.
- C4 Store: Qdrant 3 shards × 2 replicas (16 vCPU / 64 GB / NVMe each) — fits a CELS/Spark box.
- C5 Lexical: OpenSearch 3 nodes (or co-located Tantivy).
- C6 Embedding: 1 GPU (uicgpu/Sophia) batch worker — vastly over-provisioned for the load.
- C8 Redis: 3-node cluster (4 vCPU / 16 GB).
- LLM extraction: free Argo/Sophia/CELS with batching + backpressure.

---

## 8. SLOs
- Recall p95 ≤ 150 ms (cached) / ≤ 400 ms (cold). 
- Capture accept p99 ≤ 50 ms (bus enqueue).
- Extraction freshness: L1 available ≤ 2 min after trigger (p95).
- Availability: 99.5% gateway/recall; durable bus (no L0 loss).
- Data durability: L0 never dropped (at-least-once + object-store archive).

---

## 8.5 Consistency model (guarantees)
- **Capture = durable-on-ack:** once a write is acknowledged it is on the bus and never lost (at-least-once + object-store archive). Ack target < 10 ms.
- **Recall = eventually consistent:** an agent's own new memory is recallable within seconds of L1; cohort/`all`-scope cross-agent recall is consistent within the aggregation window (< 30 s).
- **No cross-agent write contention:** the bus is partitioned by `agent_id`, so per-agent ordering is preserved and there is no lock contention between agents' writes.

## 8.6 Acceptance Criteria (Definition of Done)
The system is "done" when all 8 gates pass under load test:
1. **Concurrent writers:** 1,000 concurrent agents capturing, capture-ack < 10 ms, zero message loss.
2. **Recall latency:** recall p99 < 100–150 ms under sustained load.
3. **Fleet query:** any single agent's memory is fleet-queryable via `all` scope in < 30 s.
4. **Federated search:** cross-agent search returns a merged + deduped result set.
5. **Pipeline drain:** the extraction pipeline reaches and holds steady state (no unbounded backlog) at target ingest rate.
6. **Graceful degradation:** if the aggregation tier is lost, the system degrades cleanly to per-agent self-recall (no hard failure).
7. **Capacity table:** a published {nodes × partitions × workers} → sustained-agent-count table, validated by load test.
8. **Supply chain:** SBOM is clean — US/allied origin only, no Tencent/China-origin runtime dependencies.

## 9. Deployment topology & HA
- Containerized (Docker/Podman); orchestrate via k8s or systemd fleet on CELS/DGX nodes.
- Stateless tiers (gateway, workers) scale horizontally; stores replicated + sharded.
- Backups: nightly store snapshot → S3/MinIO; JSONL L0/L1 archive retained per retention policy.
- DR: cross-node replication; restore-from-snapshot runbook.

---

## 10. Security & data residency
- All components US-OSS, self-hosted on Argonne/CELS infra — no Tencent Cloud egress.
- Per-tenant isolation (namespace + ACL); private tier never cross-agent readable.
- Embeddings + LLM on on-prem Argo (free, no China dependency).
- SBOM + pinned deps; secrets via keychain/1Password/env-file (never in code/chat).
- Audit log of all swarm promotions (provenance-kept).

---

## 11. Migration into this spec (from today)
- Reuse `IMemoryStore` abstraction → add Qdrant/pgvector adapter.
- Dual-run per SCALE plan (10→100→1,000); export current vectors.db/records/scene_blocks/persona into the shared store with parity checks; keep tool names via the gateway.

## 12. Architecture decisions (LOCKED — Rick-approved 2026-06-22 "go with your recommendations")
- **C4 vector store: Qdrant** — purpose-built for 1,000-agent vector scale (native sharding/replication/multi-tenancy). (pgvector was the alternative; not chosen.)
- **C2 bus: NATS JetStream** — already run for Sibline, lighter ops than Kafka. (Kafka not chosen.)
- **C5 lexical/BM25: Tantivy** — embedded, simplest to operate; no separate cluster. (OpenSearch not chosen.)
- **Host fleet: CELS compute nodes for the store + bus + workers** (memory/CPU-bound), reserving GPU boxes (uicgpu / Sophia / DGX) for the embedding service + LLM extraction only. Replicate Qdrant + NATS across ≥2 CELS nodes for HA.
- All four are now baked into the component table (§3) and sizing (§7). No open architecture decisions remain; next step is the Phase-0 stand-up per the migration plan.
