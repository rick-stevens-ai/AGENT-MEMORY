# Scaling the tdai Memory System to 1,000 Simultaneous Agents
### A plan for rapid, concurrent memory aggregation across a large agent swarm
*Author: Ollie (Rick Stevens / Argonne) — 2026-06-22. Grounded in live inspection of the installed `@tencentdb-agent-memory/memory-tencentdb` v1.0.0 plugin.*

---

## 0. TL;DR
The current system is a **single-node, local-first** memory engine: SQLite (FTS5 / sqlite-vec) per agent, an LLM-driven L0→L1→L2→L3 extraction pipeline, and an in-process pipeline scheduler. It already ships a **store pool with `maxStores=1000`**, a **leaderless 16-shard timer-scanner**, a **concurrency=10 pipeline worker**, and a **disabled Kafka metric producer** — i.e. the bones of a distributed system are present but unused. Scaling to 1,000 live agents that *rapidly aggregate* memories requires moving from N independent SQLite files to a **shared, sharded vector/lexical store**, fronting L0 capture with a **durable message queue**, running L1→L3 extraction in a **horizontally-scaled async worker pool**, and adding a **cross-agent aggregation tier** ("swarm memory") on top of per-agent private tiers. All of it fits on existing Argonne/CELS infrastructure.

---

## 1. Where we are today (the honest baseline)

| Dimension | Current state | Scaling implication |
|---|---|---|
| Store | One SQLite `vectors.db` per agent instance (sqlite-vec + FTS5) | File-per-agent doesn't share knowledge; SQLite single-writer lock caps concurrency |
| Retrieval | BM25/FTS5 lexical (+ optional sqlite-vec embeddings) | Lexical-only is cheap but misses semantic recall at scale |
| Extraction | In-process scheduler: every 5 conversations → L1; L2 after L1; L3 every N | In-process can't absorb 1,000 agents' throughput |
| Concurrency | pipeline-worker concurrency=10, 16-shard leaderless timer | Good primitive, but bound to one node/process |
| LLM | `argo:claude-sonnet-4.6` via ai-sdk for extraction/synthesis | Must batch + rate-limit across free Argo/Sophia/CELS endpoints |
| Aggregation | None across agents — each agent's memory is an island | The core ask: 1,000 agents must *pool* memory |
| Observability | OpenTelemetry deps present; Kafka producer disabled | Turn it on for swarm-scale visibility |

**Three hard bottlenecks to remove:** (1) SQLite single-writer per file, (2) in-process synchronous extraction, (3) no cross-agent memory fusion.

---

## 2. Target architecture (1,000-agent swarm)

```
                         ┌─────────────────────────────────────────────┐
  1,000 agents  ──L0──▶  │  Ingestion bus (Kafka / NATS JetStream)      │
  (each emits             │  topic: mem.l0.capture  (partitioned)        │
   raw turns)             └───────────────┬─────────────────────────────┘
                                          │
                          ┌───────────────▼───────────────┐
                          │  Extraction worker pool         │  (k8s / systemd fleet)
                          │  L1 extract → L2 scene → L3      │  autoscaled, idempotent
                          │  batched LLM calls (Argo/Sophia) │
                          └───────────────┬────────────────┘
                                          │ writes
                 ┌────────────────────────▼─────────────────────────┐
                 │  Shared memory store (multi-tenant)                │
                 │  • pgvector OR Qdrant — vector + payload           │
                 │  • per-agent namespace (private tier)             │
                 │  • SWARM tier (shared, aggregated)               │
                 │  • BM25/sparse via OpenSearch or Tantivy          │
                 └────────────────────────┬─────────────────────────┘
                                          │
                 ┌────────────────────────▼─────────────────────────┐
                 │  Aggregation / fusion service                     │
                 │  cross-agent dedup, conflict-resolve, rollup      │
                 │  → writes consolidated "swarm knowledge" entries  │
                 └────────────────────────┬─────────────────────────┘
                                          │ recall
       agents ◀──── hybrid search (private namespace ∪ swarm tier), cached
```

### 2.1 Shared store (replaces per-file SQLite)
- **Primary recommendation: Qdrant** (Rust, OSS, US-friendly) or **pgvector on Postgres** if we want SQL + transactional rollups in one place.
  - Qdrant: native multi-tenancy via **collections + payload-indexed `agent_id`**; HNSW vector index; horizontal sharding + replication built in.
  - pgvector: simpler ops if we already run Postgres; partition by `agent_id`; use HNSW (pgvector ≥0.7).
- **Tenancy model:** each agent = a namespace/payload key. Two logical tiers per record: `tier=private` (agent-scoped) and `tier=swarm` (shared, written by the aggregation service).
- Keeps the same logical L0/L1/L2/L3 record types; only the physical backend changes.

### 2.2 Durable ingestion bus (fronts L0)
- **Kafka** (the plugin already has a disabled Kafka metric producer — reuse the wiring) or **NATS JetStream** (lighter, we already run NATS/Sibline for Ollie↔Kukla).
- Agents publish raw turns to `mem.l0.capture`, partitioned by `agent_id` → ordered per-agent, parallel across the fleet. Decouples capture latency from extraction cost; absorbs bursts.

### 2.3 Extraction worker pool (replaces in-process scheduler)
- A horizontally-scaled fleet of stateless workers consuming the bus. Each worker runs the existing L1→L2→L3 logic but **idempotently** (keyed on conversation/message hash) so redelivery is safe.
- Reuse the **16-shard leaderless timer-scanner** concept for L2/L3 cadence, but coordinate via the store (or Redis) instead of in-process state, so shards spread across worker nodes.
- Target worker concurrency: start at 10/worker × N workers; autoscale on bus lag.

### 2.4 Cross-agent aggregation tier ("swarm memory") — the heart of "rapid aggregation"
This is what turns 1,000 memory islands into a pooled brain:
- **Dedup:** near-duplicate L1 memories across agents collapsed via embedding similarity + MinHash on text; keep one canonical, attach `seen_by=[agent_ids]` provenance.
- **Conflict resolution:** when two agents record contradictory facts, run an LLM judge (multi-judge per Rick's standing scoring rule) → mark `disputed` with both claims + evidence, never silently overwrite.
- **Rollup:** periodically synthesize agent-level scene blocks into **swarm scene blocks** (shared topics) and a **swarm persona/knowledge card**.
- **Provenance-first:** every swarm entry keeps source agent IDs + timestamps (OwnLedger discipline — the swarm tier must be auditable, not a trust-the-peer blob).
- Runs as its own service on a cadence (e.g. every M new private memories per topic) so aggregation is *rapid* without blocking capture.

### 2.5 Recall at scale
- Hybrid query = agent's private namespace **∪** swarm tier, RRF-fused (keep the existing hybrid strategy).
- **Latency budget ≤ 150 ms p95** for recall injection. Achieve via: HNSW ANN, a **Redis recall cache** keyed on (agent_id, query-embedding-bucket), and capping `maxResults`/`maxTotalRecallChars` as today.
- Shard the store by `agent_id` hash; swarm tier replicated read-mostly.

---

## 3. Capacity math (sizing the swarm)

Assumptions (flagged ASSUMPTION — tune with real telemetry):
- ASSUMPTION: 1,000 agents, ~200 conversation turns/agent/day → 200k L0 msgs/day (~2.3 msg/s avg, ~10× burst).
- ASSUMPTION: L1 extraction fires every 5 conversations → ~40k L1 extractions/day (~0.5/s avg).
- ASSUMPTION: ~3 memories/extraction → ~120k new memory records/day.
- Embeddings (if enabled at 1536-dim): 120k/day ≈ 1.4/s avg; trivially batchable. One A100 batching an OSS embedder does >>10k embeddings/s — **embedding is not the bottleneck**; LLM extraction is.
- LLM extraction: ~40k calls/day ≈ 0.5/s sustained. Across free Argo/Sophia/CELS this is comfortable with batching + backpressure; reserve headroom for bursts.
- Storage: 120k records/day × ~2 KB (text + 1536×4B vector ≈ 6 KB with vector) ≈ ~1 GB/day raw → ~365 GB/yr before dedup; swarm dedup should cut private→swarm duplication substantially.

Conclusion: **the LLM extraction rate and recall latency are the design constraints, not raw storage or embedding throughput.** Both are addressed by the worker pool + cache + batching.

---

## 4. Concurrency & correctness
- Remove SQLite single-writer entirely (shared store handles concurrent writes).
- All extraction idempotent (hash-keyed upserts) so the at-least-once bus is safe.
- Per-agent ordering preserved by partitioning the bus on `agent_id`.
- Aggregation writes are append-mostly with explicit conflict states — no destructive cross-agent overwrites (preserves the single-writer-of-truth principle at the *record* level even with many producers).

---

## 5. Observability
- Turn on the existing OpenTelemetry traces/logs + the dormant Kafka metric producer.
- Dashboards: bus lag, extraction p95, recall p95, store QPS, dedup ratio, conflict rate, per-agent memory growth.
- Alerting on extraction backlog and recall-latency SLO breaches.

---

## 6. Phased rollout
- **Phase 0 (1–2 wk):** Stand up Qdrant/pgvector + NATS/Kafka on existing infra. Build a store-adapter so the plugin can target the shared store instead of local SQLite (the abstraction layer already exists — `IMemoryStore`).
- **Phase 1 — 10 agents:** Dual-run (local SQLite + shared store) for 10 agents; verify parity of recall results; validate idempotent extraction.
- **Phase 2 — 100 agents:** Move extraction off-process into the worker pool; enable the bus; introduce the swarm aggregation service in shadow mode (compute but don't inject).
- **Phase 3 — 1,000 agents:** Enable swarm-tier recall injection; autoscale workers; turn on full observability + SLOs; decommission per-agent SQLite for migrated agents.

---

## 7. Hardware on our existing footprint
- **Store:** Qdrant/Postgres on a CELS node or a Spark/DGX box (memory-bound, not GPU); replicate for HA.
- **Bus:** NATS JetStream (already used for Sibline) or a small Kafka cluster.
- **Workers:** CPU fleet (CELS compute-11..15 / DGX CPU) — extraction is LLM-API-bound, not local-GPU-bound.
- **Embeddings (if enabled):** batch on uicgpu (8×A100) or Sophia — massive headroom.
- **LLM extraction:** free Argo/Sophia/CELS endpoints with batching + backpressure (per Rick's free-endpoint-only policy).

---

## 8. Risks
- Cross-agent privacy/leakage: the swarm tier must enforce that private-tier entries are only promoted via the aggregation service with provenance, never raw-shared. Add per-agent ACLs on namespaces.
- Conflict storms: 1,000 agents can generate contradictory facts fast — the multi-judge conflict resolver must be rate-limited and cache verdicts.
- LLM cost/limits: stay on free endpoints; backpressure on extraction when endpoints saturate rather than dropping data.
- Migration data-loss: dual-run + checksum parity before decommissioning any SQLite file.
