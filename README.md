# A-Ver — Trademark Verification Engine

A-Ver is an independent trademark evidence-resolution engine. It is intentionally separated from marketplace discovery, creative generation, source acquisition, delivery, and any caller-specific business workflow.

## Current state

`ACCEPTANCE_ONLY` — A-Ver is proving resolver capabilities on GitHub-hosted runners. Acceptance evidence cannot produce a production trademark PASS/KILL/HOLD for an external engine until the explicit promotion gate is completed.

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