# A-Ver — Trademark Verification Engine

A-Ver is an independent trademark evidence-resolution engine. It is intentionally separated from marketplace discovery, creative generation, source acquisition, delivery, and any caller-specific business workflow.

## Current state

`PRODUCTION_APPROVED_SCOPED` — A-Ver may emit scoped production `TM_PASS` / `TM_HOLD` / `TM_KILL` receipts through its versioned interface. `CURRENT.json` and `spec/engine.json` are the machine authority; production callers must bind an exact approved A-Ver commit rather than track mutable `main`. A-Ver does not authorize a caller's live gate or external side effects: Daily7 owns its own G7 live authorization and validates the exact-pin receipt before changing caller state.

## Authority

Runtime authority is, in order:

1. `CURRENT.json`
2. `spec/engine.json`
3. the exact A-Ver commit SHA used for execution
4. immutable GitHub Actions run/artifact evidence

Conversation history, caller state, search-engine snippets, and prior run summaries are not runtime authority.

## Resolver roles

- **Trademarkia** — broad U.S. federal-record resolver when its native result set and material records are machine-resolved.
- **TMHunt** — IC025/apparel-adjacent resolver. Its scope may not be generalized to Class 016 or to all federal marks.
- **USPTO/TSDR web** — optional targeted official spot verification when a serial or registration identifier is already known and the surface is reachable.

A resolver's transport success is not trademark clearance. A search miss is not a zero-result proof. Positive credible evidence may escalate asymmetrically; negative clearance requires resolved scope and result-set semantics.

## Isolation

A-Ver never writes to external repositories, Google Drive, marketplace ledgers, or caller state. It produces evidence receipts only. Callers decide how to consume those receipts under their own safety doctrine.

See `docs/ARCHITECTURE.md` and `spec/engine.json`.