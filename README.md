# AGENT-MEMORY

Working documents for the **combined agent-memory stack** — the durable, cross-agent memory
system behind long-lived AI agents (Ollie on CherryRd, Kukla on an M1 Mac mini) at Argonne.

The stack has three cooperating layers:

1. **TDAI** — the live four-layer (L0→L1→L2→L3) capture/distill/recall runtime (today's canonical system).
2. **STRATUS** — a born-clean, US-origin standalone re-implementation hardened for 1,000-agent multi-tenant scale (planned successor, currently shadow dual-run).
3. **UMP** — a schema-first cross-agent reference store (shared facts, record schema, memory policy).

The guiding principle: **memory augments file-backed truth; it never replaces it.**

---

## Start here

- **[The Combined Agent-Memory Stack — White Paper](whitepaper/WHITEPAPER-combined-memory-stack.pdf)**
  ([Markdown source](whitepaper/WHITEPAPER-combined-memory-stack.md)) — the integrated narrative
  of how TDAI, STRATUS, and UMP work together.

## Contents

| Folder | Contents |
|---|---|
| `whitepaper/` | The combined-stack white paper (PDF + Markdown). |
| `tdai/` | Ground-truth architecture brief of the live TDAI runtime; deck generator. |
| `specs/` | The 1,000-agent engineering spec, scale plan, and US-rebuild/migration plan. |
| `stratus/` | (Pointer) STRATUS is its own repo — see Related repositories. |
| `ump/` | UMP record schema, README, and cross-agent integration docs. |
| `decks/` | Presentation decks: TDAI system, STRATUS (System + Scaling), combined. |

## Key documents

- `tdai/ARCHITECTURE_BRIEF.md` — source-of-truth architecture read from the live installed plugin.
- `specs/SYSTEM-SPEC-1000-AGENTS.md` — buildable engineering spec (components, schemas, APIs, SLOs, acceptance gates).
- `specs/SCALE-1000-AGENTS-PLAN.md` — strategy for scaling to 1,000 concurrent agents with swarm aggregation.
- `specs/US-REBUILD-MIGRATION-PLAN.md` — provenance/clean-room rebuild plan.
- `ump/record-schema.md` — the cross-agent memory record schema.

## Related repositories

- **STRATUS** (born-clean US-origin memory system, Apache-2.0): https://github.com/rick-stevens-ai/stratus
- **UMP** (reference cross-agent memory store): https://github.com/rick-stevens-ai/ump-memory
- **reasoning-safe-client** (companion: safe handling of reasoning-model outputs, MIT): https://github.com/rick-stevens-ai/reasoning-safe-client

---

*Rick Stevens, Argonne National Laboratory. Compiled 2026-06-25.*
