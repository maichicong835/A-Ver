# A-Ver Architecture

## 1. System boundary

A-Ver has one responsibility: **resolve trademark evidence and produce a reconstructable trademark verification receipt**.

A-Ver does not own market discovery or demand ranking; buyer segment/JTBD; entertainment K5A/K5B; copyright/provenance; source-image acquisition or transformation; creative generation; Google Drive delivery; Used/Reserve ledgers; or any caller's terminal portfolio state.

The caller supplies wording/query context as data. The caller never becomes A-Ver authority.

## 2. Authority graph

`CURRENT.json` -> `spec/engine.json` -> exact Git commit -> GitHub Actions execution -> immutable Actions artifact receipt.

No second spec is allowed inside workflow prompts. Workflows are transports/orchestrators and must read the engine contract rather than replicate trademark doctrine.

Authority or documentation changes do not, by themselves, invalidate already proven resolver capability. Closed acceptance phases therefore do not auto-rerun merely because `CURRENT.json`, `spec/**`, documentation, or shared contract tests changed. A phase auto-runs when its own harness/workflow changes; manual `workflow_dispatch` remains available for deliberate revalidation.

## 3. Truth separation

A-Ver keeps these layers separate:

1. `TRANSPORT_TRUTH` — can this execution surface reach the resolver?
2. `QUERY_EXECUTION_TRUTH` — was the intended native query actually submitted?
3. `RESULTSET_TRUTH` — was the native result set resolved, including zero semantics when applicable?
4. `RECORD_BINDING_TRUTH` — can material hits be bound to identifiers/status/class/G&S?
5. `SCOPE_COVERAGE_TRUTH` — what registry/classes/query modes did this resolver actually cover?
6. `SIMILARITY_ANALYSIS_TRUTH` — exact/core/phonetic/semantic/commercial-impression analysis.
7. `GOODS_RELATEDNESS_TRUTH` — class and G0-G4 relatedness.
8. `TM_DECISION_TRUTH` — PASS/KILL/HOLD, available only after production promotion.

A lower layer may block higher layers, but it may never impersonate them.

## 4. Resolver roles

### Trademarkia

Trademarkia is the broad U.S. federal-record discovery resolver. Positive material records can escalate review once record binding is proven. Its search surface can fuzzy-expand or tokenize multi-word queries, so an opaque-token `No results` result proves negative semantics only for that machine-bound query behavior. It does **not** establish exact negative clearance for arbitrary multi-token wording.

### TMHunt

TMHunt is the IC025/apparel-adjacent resolver. It is valuable because many slogan/sticker mechanisms overlap apparel channels, but IC025 evidence must never be generalized to Class 016 or the entire federal registry. Exact/Partial/Split/Wildcard modes are separate capabilities.

Machine-proven TMHunt negative evidence remains bounded to IC025 unless future machine evidence proves broader scope.

### USPTO/TSDR web

USPTO/TSDR web remains an optional targeted official spot verifier when a serial/registration identifier is already known. A-Ver does not require privileged API credentials for its base architecture.

## 5. Evidence asymmetry

A credible positive hit is information-rich and may immediately escalate review. A negative claim is information-poor unless the native result set, query scope, filters, and resolver scope are proven.

Therefore:

`positive hit -> bind -> analyze`

but:

`search miss -> no inference`

and:

`native resolved zero + sufficient required scope -> eligible negative evidence`.

A material positive hit is never cancelled by a negative from another resolver. Resolver outputs do not form a vote. Negative evidence carries only the scope machine-proven for that resolver.

## 6. Acceptance state machine and current closure

A0 Transport -> A1 Known Positive -> A2 Query/Resultset Semantics -> A3 Negative Semantics -> A4 Repeatability -> Promotion Review.

Current authoritative closure:

- A0: `PASS_CLOSED`
- A1: `PASS_CLOSED`
- A2: `PASS_CLOSED`
- A3: `PASS_CLOSED`
- A4 Trademarkia behavior matrix: `PASS_CLOSED`
- A4 TMHunt Exact zero semantics: `PASS_CLOSED`
- A4 TMHunt positive Exact/Partial/Split/Wildcard result binding: `OPEN / UNPROVEN`

Acceptance states are capability states only. They cannot be serialized as TM PASS/KILL/HOLD for an external workflow.

A failed or incomplete phase reopens only the failed component. Successful prior phases remain closed unless their evidence is materially invalidated by a resolver surface, harness, scope, or semantics change.

## 7. A4 bounded closure contract

The next acceptance work is intentionally narrow: **TMHunt positive mode result binding only**. No new resolver, market phrase, Daily7 wording, or canary breadth is allowed as a repair mechanism.

For Exact/Partial/Split/Wildcard positive modes, A4 must prove all of the following:

- active mode is machine-attested after interaction; `clicked=true` alone is insufficient;
- query submission is scoped to the active search panel;
- a fixed sleep is not the only completion signal;
- the harness waits for a bounded terminal DOM state: structured positive results, explicit zero, or explicit control/failure state;
- a positive resultset may be proven by one or more structured bound result rows even if a specific `Showing ... results` count string is absent;
- bounded evidence includes final URL, query binding, active-mode attestation, result/table structure, a small result-row sample, count/pagination metadata when available, and a structural/body hash.

One causal repair is allowed. If the same resolver + same A4 stage + same failure signature persists, A-Ver must hold that capability and stop the same-strategy loop.

## 8. Anti-loop controller

The same resolver + stage + failure signature may be retried once after a causal repair. A repeated identical failure forbids more same-strategy retries. The next action must change a causal dimension or terminate that capability as unresolved.

Adding more candidate phrases is never a valid repair for a systemic resolver transport, mode-binding, or resultset failure.

Successful prior layers remain closed. Authority/doc edits are not capability invalidation events.

## 9. A4 repeatability law

A4 full mode-matrix PASS is only the first repeatability observation. Before promotion, A-Ver requires a second distinct GitHub workflow run using:

- the same exact commit SHA;
- the same A4 harness;
- the same fixed canaries;
- no code/spec/authority change between the two runs;
- `workflow_dispatch` for the second execution;
- matching normalized semantic states.

Re-running a job inside the same workflow run is insufficient. Touching a trigger file or making a no-op commit is also insufficient because it changes the commit identity being tested.

## 10. Runtime evidence

Runtime receipts are uploaded as GitHub Actions artifacts rather than committed back into the repository. This prevents runtime evidence from mutating specification authority and prevents self-triggering commit loops.

Every receipt binds the exact A-Ver commit SHA and workflow run ID. Raw public page bodies are hashed but not persisted by default; only minimal structural evidence required for reconstructability is stored.

## 11. Production transition design lock

Acceptance scripts must not become a disposable proof layer followed by an unrelated production reimplementation. After A4 repeatability, proven interaction and parsing primitives must be extracted into shared resolver modules. Both acceptance and production workflows must call the **same resolver implementation**.

The intended shape is:

`proven acceptance primitives -> shared resolver modules -> acceptance tests + production workflow`

not:

`acceptance implementation -> separately rewritten production implementation`.

Before production promotion, A-Ver also requires a versioned request schema and versioned receipt schema. A generic `safe=true` output is forbidden because A-Ver owns trademark evidence/decision only, not entertainment, copyright, persona, marketplace policy, or overall product safety.

## 12. Future caller integration

After promotion, callers should pin A-Ver to an exact approved commit or release rather than track mutable `main`.

The preferred contract is:

`caller request data -> pinned A-Ver resolver -> versioned TM receipt -> caller independently validates receipt -> caller mutates only its own state`.

The request contains data such as request ID, wording, intended-goods context, requested scope, caller reference, and contract version. The receipt binds A-Ver version/commit, request hash, query plan, resolver scopes used, material records, identifiers/status/classes/G&S, unresolved dimensions, TM decision, and evidence hashes.

Cross-repository state mutation remains forbidden. Daily7 or any other caller must not import A-Ver internal state or resolver UI logic.

## 13. Promotion law

Acceptance success does not silently make production changes. Production requires a separate promotion commit that changes `CURRENT.json` and `spec/engine.json` from `ACCEPTANCE_ONLY` to the explicitly reviewed production state.

Promotion requires full A4 mode-matrix PASS, two distinct repeatable GitHub runs on the same exact commit, documented resolver scopes, shared resolver primitives, versioned request/receipt contracts, no control circumvention, explicit user approval, and the separate promotion commit.

Until then, production TM decisions and Daily7 integration are forbidden.

## 14. Operational authority protection

Caller pinning to an exact approved A-Ver commit/release is the primary anti-drift boundary because it prevents a later mutable `main` commit from silently changing caller behavior.

Before external production use, repository-side authority protection should also be hardened with appropriate branch/ruleset and required contract checks where available. This is defense in depth; it does not replace exact caller pinning.
