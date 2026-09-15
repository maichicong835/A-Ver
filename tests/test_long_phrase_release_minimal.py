#!/usr/bin/env python3
from aver.positive_recall import classify_expanded_partial_recall
from aver.query_plan import STOPWORDS, derive_fallback_core_queries
from aver.uspto_fieldtag_direct_canary import result_count_from_body, single_record_detail_from_body


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


def test_uspto_auto_opened_single_result_is_machine_bound():
    body=(
        "Result 1 of 1 for CM:(/creating/ AND /spreadsheet/) "
        "Search result details for serial number 77348348 "
        "Trademark Wordmark EXAMPLE MARK Serial number 77348348 "
        "Registration number 1234567 Filing date January 1, 2000 "
        "Status DEAD Status date January 1, 2020 "
        "Goods and services Class 009 computer software Current owner Example Owner "
        "Case status Dead Publication date January 1, 2001"
    )
    count=result_count_from_body(body)
    detail=single_record_detail_from_body(body,count)
    assert count==1, count
    assert detail["serial_number"]=="77348348", detail
    assert detail["mark_text"]=="EXAMPLE MARK", detail
    assert detail["class_codes"]==["009"], detail


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
    test_uspto_auto_opened_single_result_is_machine_bound()
    test_dead_unrelated_partial_is_narrowly_nonmaterial()
    test_exact_positive_never_uses_partial_nonmaterial_exception()
    print("LONG_PHRASE_RELEASE_MINIMAL_CONTRACTS_PASS")
