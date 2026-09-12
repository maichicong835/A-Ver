# A-Ver Architecture

## 1. System boundary

A-Ver has one responsibility: **resolve trademark evidence and produce a reconstructable trademark verification receipt**.

A-Ver does not own market discovery or demand ranking; buyer segment/JTBD; entertainment K5A/K5B; copyright/provenance; source-image acquisition or transformation; creative generation; Google Drive delivery; Used/Reserve ledgers; or any caller's terminal portfolio state.

The caller supplies wording/query context as data. The caller never becomes A-Ver authority.

## 2. Authority graph

`CURRENT.json` -> `spec/engine.json` -> exact Git commit -> GitHub Actions execution -> immutable Actions artifact receipt.

No second spec is allowed inside workflow prompts. Workflows are transports/orchestrators and must not replicate trademark doctrine.

Closed acceptance phases do not auto-rerun merely because CURRENT/spec/docs change. Resolver acceptance, contract-state testing and authority validation are separate jobs.

## 3. Truth separation

A-Ver keeps transport, query execution, resultset, record binding, scope coverage, similarity, goods-relatedness and TM decision as separate truth layers. A lower layer may block a higher layer but may never impersonate it.

Capability PASS is not TM PASS. Search-engine absence is not native zero. Transport failure has zero candidate-risk weight. An unbound query has zero negative-clearance weight.

Workflow success must reflect semantic phase success; a PARTIAL acceptance receipt may be uploaded for evidence, but the workflow must not finish green.

## 4. Resolver roles

### Trademarkia

Trademarkia is the broad U.S. federal-record discovery resolver. It provides broad recall and can fuzzy-expand/tokenize multi-word queries. Positive material records may escalate review when bound to record details.

Opaque single-token `No results` semantics are accepted only with limited meaning and may never be generalized into arbitrary multi-token exact negative clearance.

The public search surface can re-render during page hydration. Therefore A-Ver requires stable query binding before submission: the exact query value must be machine-observed twice after binding, with at most three bounded re-bind attempts. If binding is unstable, the query is not submitted and the capability holds.

### TMHunt

TMHunt is an IC025/apparel-adjacent resolver. IC025 evidence must never be generalized to Class 016 or to the full federal registry.

Machine-proven declared capability:

- Exact positive binding: PASS
- Partial positive binding: PASS
- Exact native zero semantics: PASS
- Split: excluded/unproven, zero coverage weight
- Wildcard: excluded/unproven, zero coverage weight

Split and Wildcard are not retried with the same strategy and contribute no evidence unless a future deliberate capability-development cycle is separately authorized.

### USPTO/TSDR web

USPTO/TSDR web remains an optional targeted official spot verifier when a serial/registration identifier is already known. A-Ver does not require privileged API credentials for its base fallback architecture.

## 5. Evidence asymmetry

A credible positive hit may immediately escalate review. Negative evidence is usable only inside the machine-proven query and resolver scope.

A material positive hit is never cancelled by a negative from another resolver. Resolver outputs are not votes.

An excluded or unproven capability contributes no positive evidence, no negative evidence and no scope coverage.

For an operational negative PASS, the required query dimensions and required resolver scope must be complete and negative evidence must converge across at least two distinct evidence sources. This is still not a legal-clearance claim.

## 6. Acceptance closure

A0 Transport, A1 Known Positive Binding, A2 Query/Resultset Semantics and A3 Negative Semantics are `PASS_CLOSED`.

A4 is also now `PASS_CLOSED` for declared capability profile repeatability.

The closing pair used the same exact commit:

`adb32a9b554a420f9dedc1c6d2916bcaec16d9b6`

with harness revision:

`a4.3-query-binding-stability`

and two distinct workflow runs:

- `34702194480` -> `A4_DECLARED_PROFILE_PASS`
- `34702254867` -> `A4_DECLARED_PROFILE_PASS`

The normalized capability states matched across both runs. TMHunt Split/Wildcard were not retested. No Daily7 candidate query or production TM decision was authorized during A4.

## 7. Why full website feature coverage is not the target

The production objective is complete required TM analysis, not completion of every UI control a resolver happens to expose.

`resolver UI mode != TM query-plan stage`.

Required query stages remain Exact, normalized exact, core/dominant token, expanded/partial, phonetic/spelling when material and related-goods review. They may be completed by different authorized resolvers according to their proven capabilities.

If authorized capabilities cannot complete a required query dimension, A-Ver must return `TM_HOLD_EVIDENCE`; missing evidence may never be silently treated as covered.

## 8. Anti-loop law

One causal repair is allowed for one observed causal dimension. Candidate breadth, new resolvers or unrelated parser changes are not valid responses to a systemic transport, binding or repeatability failure.

The A4 repeatability failure on run `34701579192` was traced to an empty pre-submit Trademarkia input. The repair changed only stable query binding; the post-repair pair then reproduced cleanly.

Closed resolver acceptance is not reopened by status/documentation/interface-contract changes unless a material resolver surface, harness or semantics invalidation is machine-established.

Contract status updates do not retrigger resolver acceptance. Contract-matrix status updates do not retrigger the contract matrix.

## 9. Versioned external interface

Before promotion, A-Ver defines a versioned interface:

- request schema: `spec/request.schema.json`, version `1.0`
- receipt schema: `spec/receipt.schema.json`, version `1.0`
- deterministic decision controller: `src/aver/decision.py`
- semantic state matrix: `tests/test_contract_matrix.py`

The request contains data only: wording, intended-goods context, requested U.S. federal scope and caller reference. It cannot inject engine authority or policy.

The receipt binds the exact engine commit and request hash and carries TM decision, reason codes, query-plan state, resolver evidence, material records, unresolved dimensions, scope coverage, similarity, goods-relatedness and evidence hashes.

A generic `safe=true` output is forbidden. `legal_clearance_asserted` must always be false.

## 10. Deterministic TM decision law

The pre-promotion controller is deliberately conservative:

- material positive record + complete record binding + material similarity + material goods relatedness -> `TM_KILL`;
- incomplete record binding, unresolved required dimensions, scope gaps, transport/control blocks or source discordance -> `TM_HOLD`;
- one negative source alone -> `TM_HOLD`;
- `TM_PASS` requires complete required query dimensions, complete required resolver scope, no material conflict and at least two distinct convergent negative evidence sources;
- `TM_PASS` is labeled `FALLBACK_HIGH_CONFIDENCE`, not legal clearance.

A material positive is never cancelled by negative evidence from another resolver.

## 11. Contract matrix

The contract matrix is a pure deterministic test. It does not contact Trademarkia, TMHunt, USPTO, Daily7 or any marketplace.

It covers at least:

- material positive conflict;
- incomplete positive record binding;
- unresolved positive similarity/goods review;
- transport block;
- control block;
- missing required query dimension;
- incomplete resolver scope;
- explicit unresolved dimensions;
- single-source negative evidence;
- source discordance;
- unresolved similarity;
- unresolved goods relatedness;
- complete convergent negative PASS;
- request schema validation;
- receipt schema validation;
- caller-authority rejection;
- generic `safe` field rejection.

The Contract Matrix workflow is isolated from resolver acceptance and triggers only when the schemas, decision controller, matrix test or its own workflow changes.

## 12. Runtime evidence

Resolver acceptance receipts are GitHub Actions artifacts, not repository commits. This keeps execution evidence separate from specification authority and prevents self-triggering receipt loops.

A4 repeatability closure artifacts:

- run `34702194480`, artifact `10300745366`, digest `sha256:27cca92464c23cdeb7cba73cc412d3b884f132fed949d5daf670b94f1c6b7ff4`
- run `34702254867`, artifact `10300339408`, digest `sha256:7f64025e65f8f2f64ae3dcb0b4fa8c9460dddc15198af749ec72f1ea537e42fb`

## 13. Daily7 integration path

Daily7 integration remains forbidden before production promotion.

After promotion, Daily7 should pin an exact approved A-Ver commit or release and send versioned request data only. A-Ver returns a versioned TM receipt. Daily7 independently validates A-Ver identity, schema and receipt, then applies its own V3.3 gates.

Daily7 keeps K5A/K5B, real-person/character, copyright/provenance, Amazon/content, market, source, focus, portfolio, Drive and ledger authority. A-Ver never mutates Daily7 state.

The first integration must be shadow-only using a tiny set of existing HOLD canaries: no Drive, Used/Reserve, source/focus or portfolio-state mutation. Live TM gating may be enabled only after shadow receipts are validated.

## 14. Promotion law

Promotion requires A0-A4 closed PASS; explicit zero-weighting of excluded modes; complete required TM query-plan coverage or HOLD; shared resolver primitives; versioned request/receipt schemas; machine-passed full contract-state coverage; documented scopes; no control circumvention; explicit user approval; and a separate promotion commit.

Until then `ACCEPTANCE_ONLY` and `production_tm_decisions_authorized=false` remain mandatory.

## 15. Authority protection

Resolver acceptance workflows, the contract matrix and authority validation remain separate. `CURRENT/spec/docs/tests` status changes invoke Authority Guard, not resolver acceptance.

Caller pinning to an exact approved A-Ver commit or release is the primary anti-drift boundary. Repository branch/ruleset protection and required checks should be enabled before external production use where available as defense in depth.
