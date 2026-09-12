# A-Ver Architecture

## 1. System boundary

A-Ver has one responsibility: **resolve trademark evidence and produce a reconstructable trademark verification receipt**.

A-Ver does not own:
- market discovery or demand ranking;
- buyer segment/JTBD;
- entertainment K5A/K5B;
- copyright/provenance;
- source-image acquisition or transformation;
- creative generation;
- Google Drive delivery;
- Used/Reserve ledgers;
- any caller's terminal portfolio state.

The caller supplies wording/query context as data. The caller never becomes A-Ver authority.

## 2. Authority graph

`CURRENT.json` -> `spec/engine.json` -> exact Git commit -> GitHub Actions execution -> immutable Actions artifact receipt.

No second spec is allowed inside workflow prompts. Workflows are transports/orchestrators and must read the engine contract rather than replicate trademark doctrine.

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
Broad U.S. federal-record resolver. A-Ver may use positive material records as soon as record binding is proven. Negative evidence is forbidden until A3 proves native negative-result semantics.

### TMHunt
IC025/apparel-adjacent resolver. It is valuable because many slogan/sticker mechanisms overlap apparel channels, but IC025 evidence must never be generalized to Class 016 or the entire federal registry. Exact/Partial/Split/Wildcard modes are validated independently.

### USPTO/TSDR web
Optional targeted official spot verifier when a serial/registration identifier is already known. A-Ver does not require privileged API credentials for its base architecture.

## 5. Evidence asymmetry

A credible positive hit is information-rich and may immediately escalate review. A negative claim is information-poor unless the native result set, query scope, filters, and resolver scope are proven.

Therefore:

`positive hit -> bind -> analyze`

but:

`search miss -> no inference`

and:

`native resolved zero + sufficient required scope -> eligible negative evidence`.

This is evidence asymmetry, not source preference.

## 6. Acceptance state machine

A0 Transport -> A1 Known Positive -> A2 Query/Resultset Semantics -> A3 Negative Semantics -> A4 Repeatability -> Promotion Review.

Acceptance states are capability states only. They cannot be serialized as TM PASS/KILL/HOLD for an external workflow.

A failed phase reopens only that phase. Successful previous phases remain closed unless their evidence is invalidated by a material surface change.

## 7. Anti-loop controller

The same resolver + stage + failure signature may be retried once. A repeated identical failure forbids more same-strategy retries in that run. The next action must change a causal dimension such as transport (HTTP vs normal browser automation) or terminate that capability as unresolved.

Adding more candidate phrases is never a valid repair for a systemic resolver transport/resultset failure.

## 8. Runtime evidence

Runtime receipts are uploaded as GitHub Actions artifacts rather than committed back into the repository. This prevents runtime evidence from mutating specification authority and prevents self-triggering commit loops.

Every receipt binds the exact A-Ver commit SHA and workflow run ID. Raw public page bodies are hashed but not persisted by default; only minimal structural evidence required for reconstructability is stored.

## 9. Future production integration

After promotion, callers should pin A-Ver to an exact commit or release. A-Ver should accept a versioned JSON input and return a versioned JSON receipt. Cross-repository state mutation remains forbidden.

The preferred long-term integration is a pinned reusable workflow/action or an explicitly authenticated A-Ver dispatch interface. In either model, A-Ver returns evidence only; the caller mutates only its own state after independently validating the receipt.

## 10. Promotion law

Acceptance success does not silently make production changes. Production requires a separate promotion commit that changes `CURRENT.json` and `spec/engine.json` from `ACCEPTANCE_ONLY` to the explicitly reviewed production state. That commit must name accepted resolver scopes and accepted negative-evidence semantics. Until then, production TM decisions are forbidden.