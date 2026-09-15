#!/usr/bin/env python3
from aver.positive_recall import classify_expanded_partial_recall
from aver.query_plan import STOPWORDS, derive_fallback_core_queries


def test_contraction_safe_cores():
    rows=derive_fallback_core_queries("I'M SILENTLY CREATING A SPREADSHEET FOR THAT")
    cores=[x["query"] for x in rows]
    assert cores
    assert all(" M " not in f" {x} " and not x.startswith("M ") for x in cores), cores
    assert all(2 <= len(x.split()) <= 3 for x in cores), cores
    assert all(x.split()[0] not in STOPWORDS and x.split()[-1] not in STOPWORDS for x in cores), cores


def test_long_phrase_has_bounded_cores():
    rows=derive_fallback_core_queries("MAYBE WITH ENOUGH SPREADSHEETS LIFE WILL MAKE SENSE")
    cores=[x["query"] for x in rows]
    assert len(cores)==2, cores
    assert all(2 <= len(x.split()) <= 3 for x in cores), cores
    assert all(x.split()[0] not in STOPWORDS and x.split()[-1] not in STOPWORDS for x in cores), cores


def test_dead_unrelated_partial_is_narrowly_nonmaterial():
    req={"intended_goods_context":{"primary_class":"016","description":"decorative adhesive stickers"}}
    record={"serial_number":"77348348","mark_text":"EXAMPLE","class_codes":["009"],"goods_services_excerpt":"computer software"}
    body="TM5 Common Status Descriptor: DEAD/ This trademark application was refused, dismissed, or invalidated by the Office and this application is no longer active"
    out=classify_expanded_partial_recall(req,record,body,"EXPANDED_PARTIAL")
    assert out["classification"]=="NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL", out
    assert out["record_binding_complete"] is True
    assert out["legal_clearance_asserted"] is False
    assert out["common_law_clearance_asserted"] is False


def test_exact_positive_never_uses_partial_nonmaterial_exception():
    req={"intended_goods_context":{"primary_class":"016","description":"decorative adhesive stickers"}}
    record={"serial_number":"77348348","mark_text":"EXAMPLE","class_codes":["009"],"goods_services_excerpt":"computer software"}
    body="TM5 Common Status Descriptor: DEAD/ This trademark application was refused, dismissed, or invalidated by the Office and this application is no longer active"
    out=classify_expanded_partial_recall(req,record,body,"EXACT")
    assert out["classification"]=="MATERIALITY_UNRESOLVED", out


if __name__=="__main__":
    test_contraction_safe_cores()
    test_long_phrase_has_bounded_cores()
    test_dead_unrelated_partial_is_narrowly_nonmaterial()
    test_exact_positive_never_uses_partial_nonmaterial_exception()
    print("LONG_PHRASE_RELEASE_MINIMAL_CONTRACTS_PASS")
