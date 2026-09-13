#!/usr/bin/env python3
from aver.scope_semantics import REQUIRED_DIMENSIONS, resolve_dimension, evaluate_required_scope

# Native negative with correct scope can resolve a dimension.
r=resolve_dimension(dimension="EXACT",execution_state="EXECUTED",evidence_polarity="NEGATIVE",negative_semantics_scope_ok=True)
assert r["terminal_state"]=="RESOLVED_NEGATIVE"
assert r["scope_complete_for_negative_pass"] is True

# A broad or wrong-scope negative may not silently clear a required dimension.
r=resolve_dimension(dimension="EXACT",execution_state="EXECUTED",evidence_polarity="NEGATIVE",negative_semantics_scope_ok=False)
assert r["terminal_state"]=="HOLD_EVIDENCE"

# Capability failure is separate from candidate risk.
r=resolve_dimension(dimension="NORMALIZED_EXACT",execution_state="CAPABILITY_UNAVAILABLE")
assert r["terminal_state"]=="HOLD_CAPABILITY"

# Positive resultsets require bound records before escalation is considered resolved.
r=resolve_dimension(dimension="CORE_DOMINANT_TOKEN",execution_state="EXECUTED",evidence_polarity="POSITIVE",positive_record_bound=False)
assert r["terminal_state"]=="HOLD_EVIDENCE"
r=resolve_dimension(dimension="CORE_DOMINANT_TOKEN",execution_state="EXECUTED",evidence_polarity="POSITIVE",positive_record_bound=True)
assert r["terminal_state"]=="RESOLVED_POSITIVE"

# Conditional phonetic/spelling dimension may resolve only when non-materiality is machine-proven.
r=resolve_dimension(dimension="PHONETIC_OR_SPELLING_WHEN_MATERIAL",execution_state="NOT_NEEDED",material_trigger=False)
assert r["terminal_state"]=="RESOLVED_NEGATIVE"
r=resolve_dimension(dimension="PHONETIC_OR_SPELLING_WHEN_MATERIAL",execution_state="NOT_NEEDED",material_trigger=True)
assert r["terminal_state"]=="HOLD_EVIDENCE"

# Early positive conflict can stop later work but never counts as negative-scope completion.
r=resolve_dimension(dimension="RELATED_GOODS_REVIEW",execution_state="NOT_EXECUTED",material_conflict_already_proven=True)
assert r["terminal_state"]=="SKIPPED_AFTER_MATERIAL_CONFLICT"
assert r["scope_complete_for_negative_pass"] is False

# A clean negative scope requires all six dimensions resolved with scope-qualified meaning.
records=[]
for d in REQUIRED_DIMENSIONS:
    if d=="PHONETIC_OR_SPELLING_WHEN_MATERIAL":
        records.append(resolve_dimension(dimension=d,execution_state="NOT_NEEDED",material_trigger=False))
    else:
        records.append(resolve_dimension(dimension=d,execution_state="EXECUTED",evidence_polarity="NEGATIVE",negative_semantics_scope_ok=True))
summary=evaluate_required_scope(records)
assert summary["semantics_complete"] is True
assert summary["negative_scope_complete"] is True
assert summary["unresolved_dimensions"]==[]

# One unresolved required dimension must block negative-scope completion.
records[-1]=resolve_dimension(dimension="RELATED_GOODS_REVIEW",execution_state="NOT_EXECUTED")
summary=evaluate_required_scope(records)
assert summary["semantics_complete"] is True
assert summary["negative_scope_complete"] is False
assert summary["unresolved_dimensions"]==["RELATED_GOODS_REVIEW"]

print("AVER_G4A_SCOPE_SEMANTICS_PASS")
