# A-Ver Architecture

## 1. System boundary

A-Ver has one responsibility: **resolve trademark evidence and produce a reconstructable trademark verification receipt**.

A-Ver does not own market discovery or demand ranking; buyer segment/JTBD; entertainment K5A/K5B; copyright/provenance; source-image acquisition or transformation; creative generation; Google Drive delivery; Used/Reserve ledgers; or any caller's terminal portfolio state.

The caller supplies wording/query context as data. The caller never becomes A-Ver authority.

## 2. Authority graph

`CURRENT.json` -> `spec/engine.json` -> exact Git commit -> GitHub Actions execution -> immutable Actions artifact receipt.

No second spec is allowed inside workflow prompts. Workflows are transports/orchestrators and must not replicate trademark doctrine.

Closed acceptance phases do not auto-rerun merely because CURRENT/spec/docs change. Resolver acceptance and authority validation are different jobs.

## 3. Truth separation

A-Ver keeps transport, query execution, resultset, record binding, scope coverage, similarity, goods-relatedness, and TM decision as separate truth layers. A lower layer may block a higher layer but may never impersonate it.

Capability PASS is not TM PASS. Workflow success is not acceptance PASS. Search-engine absence is not native zero. Transport failure has zero candidate-risk weight.

## 4. Resolver roles

### Trademarkia

Trademarkia is the broad U.S. federal-record discovery resolver. It provides broad recall and can fuzzy-expand/tokenize multi-word queries. Positive material records may escalate review when bound to record details. Opaque single-token `No results` semantics have been machine-proven, but that result may never be generalized into exact negative clearance for arbitrary multi-token wording.

Trademarkia capability was already machine-proven and closed before the A4 TMHunt causal repair. One incidental known-positive miss in run `34700639830` does not reopen or downgrade that closed capability because no material Trademarkia surface/harness invalidation was established.

### TMHunt

TMHunt is an IC025/apparel-adjacent resolver. IC025 evidence must never be generalized to Class 016 or to the full federal registry.

After causal repair run `34700639830` on commit `2ccc13cfad2db042fcc7ffda49c640a69f3187a6`, machine evidence established:

- Exact positive binding: PASS
- Partial positive binding: PASS
- Exact native zero semantics: PASS
- Split: excluded/unproven — `TMHUNT_PANEL_SEARCH_INPUT_NOT_FOUND`
- Wildcard: excluded/unproven — `TMHUNT_PANEL_SEARCH_INPUT_NOT_FOUND`

Split and Wildcard must not be retried with the same strategy and carry **zero coverage weight** unless a future deliberate capability-development cycle is separately authorized.

### USPTO/TSDR web

USPTO/TSDR web remains an optional targeted official spot verifier when a serial/registration identifier is already known. A-Ver does not require privileged API credentials for its base fallback architecture.

## 5. Evidence asymmetry

A credible positive hit may immediately escalate review. Negative evidence is usable only within the machine-proven resolver/query scope.

A material positive hit is never cancelled by a negative from another resolver. Resolver outputs are not votes.

An excluded/unproven resolver mode contributes no evidence and no scope coverage; it is not interpreted as positive, negative, safe, or risky.

## 6. Acceptance closure after causal repair

A0 Transport -> A1 Known Positive -> A2 Query/Resultset Semantics -> A3 Negative Semantics are `PASS_CLOSED`.

A4 is now **declared capability profile + repeatability**, not a requirement to exercise every UI feature offered by every resolver.

The candidate declared profile is:

- Trademarkia: broad federal record discovery/binding, fuzzy/token recall behavior, bounded opaque-token zero semantics.
- TMHunt: IC025 Exact and Partial positive capability plus Exact zero semantics.
- TMHunt Split and Wildcard: explicitly excluded and zero-weighted.

This is a reduction of transport capability scope, **not a reduction of required TM analysis**.

## 7. Why full TMHunt UI-mode coverage is no longer the target

The production objective is complete required TM query coverage, not completion of every website control.

`resolver UI mode != TM query-plan stage`.

Required stages remain Exact, normalized exact, core/dominant token, expanded/partial, phonetic/spelling when material, and related-goods review. They may be completed by different authorized resolvers according to their proven capabilities.

If the authorized capability profile cannot complete a required query dimension for a candidate, the only valid decision is `TM_HOLD_EVIDENCE`. Missing TMHunt Split/Wildcard may never be silently substituted or treated as covered.

## 8. Anti-loop law

One causal repair was already used for the A4 TMHunt positive-binding issue. It produced real information gain: Exact/Partial changed from unproven to PASS, while Split/Wildcard exposed a different structural limitation.

The response is now capability exclusion, not another same-strategy parser/UI retry. More candidate phrases, new resolvers, or market discovery are not valid repairs.

Previously proven layers remain closed unless a material invalidation is machine-established. Incidental recheck noise from a closed component does not overwrite its proven state.

## 9. Repeatability target

Before promotion, A-Ver must freeze a **scoped A4 harness** that exercises only the declared capability profile and the fixed acceptance canaries relevant to that profile. Excluded Split/Wildcard modes are not retested.

Then A-Ver requires two distinct GitHub workflow runs using the same exact commit SHA, same scoped harness, same fixed canaries, and matching normalized semantic states. The second run should use `workflow_dispatch` without a code/spec/authority change. A same-run job retry or a no-op/trigger-file commit is insufficient.

## 10. Runtime evidence

Runtime receipts are GitHub Actions artifacts, not repository commits. This prevents self-triggering receipt loops and keeps specification authority separate from execution evidence.

The causal repair evidence is bound to:

- commit `2ccc13cfad2db042fcc7ffda49c640a69f3187a6`
- workflow run `34700639830`
- job `103571660230`
- artifact `10299693567`
- artifact digest `sha256:79e98e04c48d765ae5807901406c55fb4642761485c3bbc587d9885243a44a9c`

## 11. Production transition design lock

Acceptance code must not be discarded and rewritten independently for production. Proven resolver primitives must be extracted into shared modules and used by both acceptance and production execution.

Before promotion A-Ver requires versioned request and receipt schemas plus full contract-state coverage tests. Full testing means coverage of semantic states and failure boundaries, not increasing the number of real candidate phrases.

The contract test set must cover at least known positive, native zero, fuzzy multi-token behavior, resolver disagreement, transport failure, incomplete record binding, scope mismatch, missing required query dimension, similarity/G0-G4 HOLD, and evidence identity/hashing.

A generic `safe=true` output is forbidden. A-Ver owns trademark evidence and TM decision only.

## 12. Daily7 integration path

Daily7 integration is forbidden before promotion.

After promotion, Daily7 should pin an exact approved A-Ver commit/release and send versioned request data only. A-Ver returns a versioned TM receipt. Daily7 independently validates the A-Ver identity/schema/receipt and then applies its own V3.3 gates.

Daily7 keeps K5A/K5B, real-person/character, copyright/provenance, Amazon/content, market, source, focus, portfolio, Drive and ledger authority. A-Ver never mutates Daily7 state.

The first integration must be **shadow-only** using a tiny set of existing HOLD canaries: no Drive, Used/Reserve, source/focus or portfolio-state mutation. Live TM gating may be enabled only after shadow receipts are validated.

## 13. Promotion law

Promotion requires:

- A0-A3 closed PASS;
- declared A4 capability profile PASS;
- excluded modes explicitly zero-weighted;
- complete required TM query-plan coverage using authorized capabilities, otherwise HOLD;
- at least two repeatable runs on the same exact commit;
- shared resolver primitives;
- versioned request/receipt schemas;
- full contract-state coverage tests;
- documented resolver scopes;
- no control circumvention;
- explicit user approval;
- a separate promotion commit.

Until then `ACCEPTANCE_ONLY` and `production_tm_decisions_authorized=false` remain mandatory.

## 14. Authority protection

Resolver acceptance workflows and authority validation must remain separate. `CURRENT/spec/docs/tests` changes should invoke an Authority Guard, not rerun resolver acceptance phases.

Caller pinning to an exact approved A-Ver commit/release is the primary anti-drift boundary. Before external production use, branch/ruleset protection and required Authority Guard checks should be enabled where available as defense in depth.
