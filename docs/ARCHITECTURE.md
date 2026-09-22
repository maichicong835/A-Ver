# A-Ver Architecture

> **Current-state note (2026-09-22):** `CURRENT.json` and `spec/engine.json` are the runtime authority. Sections below that describe first-shadow, deep-shadow, G4/G5/G6 or pre-G7 gates are preserved as historical closure chronology, not as currently open production gates. A-Ver is `PRODUCTION_APPROVED_SCOPED`; caller live authorization remains caller-owned and external side effects remain forbidden.

## 1. System boundary

A-Ver has one responsibility: **resolve trademark evidence and produce a reconstructable trademark verification receipt**.

A-Ver does not own market discovery or demand ranking; buyer segment/JTBD; entertainment K5A/K5B; copyright/provenance; source-image acquisition or transformation; creative generation; Google Drive delivery; Used/Reserve ledgers; or any caller's terminal portfolio state.

The caller supplies wording/query context as data. The caller never becomes A-Ver authority.

## 2. Authority graph

`CURRENT.json` -> `spec/engine.json` -> exact Git commit -> GitHub Actions execution -> immutable Actions artifact receipt.

No second spec is allowed inside workflow prompts. Closed resolver phases, deterministic contract tests and authority validation are separate jobs.

## 3. Truth separation

A-Ver keeps transport, query execution, resultset, record binding, scope coverage, similarity, goods-relatedness and TM decision as separate truth layers. A lower layer may block a higher layer but may never impersonate it.

Capability PASS is not TM PASS. Resultset resolved is not TM PASS. Broad positive resultset is not material-conflict proof. Search-engine absence is not native zero. Transport failure and an unbound query have zero negative-clearance weight.

## 4. Resolver roles

### Trademarkia

Trademarkia is the broad U.S. federal-record discovery resolver. It provides broad recall and can fuzzy-expand/tokenize multi-word queries. Positive resultsets must be bound to concrete records and then analyzed for material similarity and goods/services relatedness before they can affect a TM decision.

Opaque single-token `No results` semantics have limited meaning and may never be generalized into arbitrary multi-token exact negative clearance. Stable query binding is required before submission: exact query value observed twice, with at most three bounded re-bind attempts.

### TMHunt

TMHunt is an IC025/apparel-adjacent resolver. Its machine-proven profile is Exact positive, Partial positive and Exact native zero within IC025. Split/Wildcard remain excluded/unproven with zero coverage weight.

**An IC025 TMHunt zero has zero Class 016 negative-convergence weight.** It may provide adjacent-market context but cannot become the second broad Class 016 negative source required for a sticker TM PASS.

### USPTO/TSDR web

USPTO/TSDR web remains an optional targeted official spot verifier when a serial/registration identifier is already known. A-Ver does not require privileged API credentials for its base fallback transport.

## 5. Evidence asymmetry

A credible positive record may immediately escalate review. A material positive is never cancelled by a negative from another resolver. Resolver outputs are not votes.

For a negative operational PASS, required query dimensions and relevant resolver scope must be complete and negative evidence must converge across at least two distinct sources relevant to the requested scope. For Class 016, Class 025-only evidence cannot satisfy that convergence requirement. `TM_PASS` remains an operational high-confidence state, not legal clearance.

## 6. Acceptance and contract closure

A0-A3 are `PASS_CLOSED`. A4 declared capability repeatability is `PASS_CLOSED` using exact commit `adb32a9b554a420f9dedc1c6d2916bcaec16d9b6`, harness `a4.3-query-binding-stability`, and independent runs `34702194480` and `34702254867`, both semantic PASS with matching normalized states.

Contract Matrix run `34702668801` on commit `6066da673117b80e10655f3833480d225dec0e0c` returned both `AVER_CONTRACT_TEST_PASS` and `AVER_CONTRACT_MATRIX_PASS`. Request and receipt schemas remain version 1.0.

## 7. Production promotion

On 2026-09-13 the user explicitly approved scoped production promotion. Production commit is `689e06afcce007979025e68a095f9646d1d37591`; Authority Guard run `34722809905` succeeded.

Promotion authorizes A-Ver to emit production TM decision states through its versioned interface. It does not authorize external side effects, cross-repository state mutation or the Daily7 live TM gate.

`production engine approval != caller live-gate approval`.

## 8. Daily7 first shadow — machine result

Daily7 pinned exact A-Ver production commit `689e06afcce007979025e68a095f9646d1d37591` and executed only two pre-existing HOLD canaries in read-only shadow workflow run `34722878035` on Daily7 head `bce20fb9db9e6ff4ff8bfbc1aa67daacbd4e1723`.

The shadow validated request schema, receipt schema, engine identity pin and no-mutation locks. Artifact `10306408819` has digest `sha256:7251ad40baf0fad95f348419cd84d24b2cc1fd23d176e1c4d2690ccf640aa036`.

Machine results:

- `I KNOW THEY SAID NURSING SCHOOL WAS HARD, BUT DAMN`: Trademarkia `POSITIVE_RESULTSET`; TMHunt IC025 `ZERO_RESULTSET`; final shadow decision `TM_HOLD`.
- `POWERED BY YARN AND CHAOS`: Trademarkia `POSITIVE_RESULTSET`; TMHunt IC025 `ZERO_RESULTSET`; final shadow decision `TM_HOLD`.

The workflow returned `AVER_DAILY7_SHADOW_PASS`. No false TM PASS occurred and no Drive, Used/Reserve, source/focus or caller-state mutation was authorized.

## 9. What the first shadow actually proved

The old systemic blocker was `TM_RESULTSET_RESOLUTION`: the execution surface could not machine-resolve official/fallback phrase resultsets. The first shadow proves that this blocker is no longer the active bottleneck for these two canaries: Trademarkia resultsets were machine-resolved for both.

This does **not** mean either wording is safe or conflicting. The bottleneck has moved upward in the truth stack to:

`material record binding -> similarity/commercial-impression analysis -> G0-G4 goods/services relatedness -> remaining required query dimensions -> scope-complete evidence convergence`.

That movement is progress because the failed layer changed from transport to interpretation, while all previously proven layers remain closed.

## 10. Current deep-shadow gate

The only open integration layer is `SHADOW_DEEP_TM_INTERPRETATION`, and it remains limited to the two existing HOLD canaries. New candidate discovery is not a valid response to this gate.

The next machine gate is:

`MATERIAL_RECORD_BINDING_SIMILARITY_G0_G4_AND_REQUIRED_QUERY_SCOPE`.

A broad Trademarkia positive resultset must be decomposed into concrete potentially material records before similarity and G0-G4 analysis. If those records or required query dimensions remain unresolved, the correct outcome is `TM_HOLD`.

For a Class 016 negative PASS, A-Ver must also establish Class-016-relevant convergent evidence. TMHunt IC025 cannot be promoted into that role merely to manufacture two-source convergence.

## 11. Anti-loop and live-gate law

One observed causal dimension gets one bounded repair. Resultset-layer shadow success does not justify reopening A0-A4, adding random resolvers, widening Daily7 candidate breadth, shifting toward V-mode candidates, or declaring no-hit safety.

The live Daily7 TM gate stays disabled until deep-shadow receipts prove identity, record binding/materiality, required query coverage, conservative decision semantics and scope-valid evidence convergence. Any unresolved material layer remains HOLD.

## 12. External interface

A-Ver request schema is `AVER_TM_REQUEST` v1.0 and receipt schema is `AVER_TM_RECEIPT` v1.0. Request data cannot inject authority. Receipts bind exact engine commit and request hash, expose reason codes/evidence/scope state, forbid a generic `safe=true`, and require `legal_clearance_asserted=false`.

Daily7 independently validates A-Ver receipts and then retains all non-TM V3.3 authority: K5A/K5B, real-person/character, copyright/provenance, Amazon/content, market, source, focus, portfolio, Drive and ledger gates.

## 13. Authority protection

Resolver acceptance, contract matrix, shadow integration and Authority Guard are distinct phases. Status/documentation changes do not reopen resolver acceptance. Runtime receipts remain immutable GitHub Actions artifacts rather than repository authority.

Caller pinning to an exact approved A-Ver commit or release is the primary anti-drift boundary. Branch/ruleset protection and required checks remain recommended defense in depth where repository permissions allow them.
