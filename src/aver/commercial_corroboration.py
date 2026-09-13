#!/usr/bin/env python3

from .resolvers.common import norm, sha


FIXED_SOURCES = {
    "NURSING_SCHOOL_JEWELS_OFFICIAL": "https://www.nursingschooljewels.com/",
    "CHAOS_BY_ELSIE_SHOPLC": "https://www.shoplc.com/pages/chaos-by-elsie",
}


def capture_fixed_commercial_source(browser, source_id, required_tokens, forbidden_control_tokens=None):
    """Capture a fixed public commercial source as hashed evidence.

    No search/discovery occurs here. The URL is frozen in code. This layer does
    not decide trademark similarity or legal clearance.
    """
    url=FIXED_SOURCES[source_id]
    rec={"source_id":source_id,"url":url,"state":"COMMERCIAL_SOURCE_UNPROVEN","required_tokens":required_tokens}
    page=browser.new_page(viewport={"width":1440,"height":1000})
    try:
        page.goto(url,wait_until="domcontentloaded",timeout=30000)
        page.wait_for_timeout(1200)
        body=norm(page.locator("body").inner_text(timeout=10000))
        lower=body.lower()
        controls=forbidden_control_tokens or ["captcha","verify you are human","are you a robot","human verification"]
        if any(x.lower() in lower for x in controls):
            rec["state"]="COMMERCIAL_SOURCE_BLOCKED"
            rec["failure_signature"]="CONTROL_OR_HUMAN_VERIFICATION_OBSERVED"
            return rec
        token_evidence=[]
        all_seen=True
        for token in required_tokens:
            seen=token.lower() in lower
            token_evidence.append({"token":token,"seen":seen})
            all_seen=all_seen and seen
        rec.update({
            "final_url":page.url,
            "token_evidence":token_evidence,
            "body_sha256":sha(page.content()),
            "body_excerpt":body[:5000],
            "body_length":len(body),
        })
        if all_seen:
            rec["state"]="COMMERCIAL_SOURCE_PASS"
        else:
            rec["failure_signature"]="REQUIRED_COMMERCIAL_EVIDENCE_TOKEN_NOT_BOUND"
    except Exception as exc:
        rec["state"]="COMMERCIAL_SOURCE_BLOCKED"
        rec["failure_signature"]=f"{type(exc).__name__}:{str(exc)[:220]}"
    finally:
        page.close()
    return rec


def evaluate_g3_g4_from_fixed_source(candidate_key, source_record):
    """Map only machine-observed commercial facts into conservative G3/G4 states."""
    if source_record.get("state")!="COMMERCIAL_SOURCE_PASS":
        return {
            "G3_CHANNELS_AND_PURCHASERS":{"state":"UNRESOLVED","material":None,"reason":"COMMERCIAL_SOURCE_NOT_MACHINE_BOUND"},
            "G4_REGISTRANT_MARKETPLACE_OR_MERCH_PRESENCE":{"state":"UNRESOLVED","material":None,"reason":"COMMERCIAL_SOURCE_NOT_MACHINE_BOUND"},
        }
    if candidate_key=="nursing-school-hard-but-damn":
        return {
            "G3_CHANNELS_AND_PURCHASERS":{"state":"RESOLVED","material":True,"reason":"BOUND_SOURCE_EXPLICITLY_TARGETS_NURSING_STUDENTS"},
            "G4_REGISTRANT_MARKETPLACE_OR_MERCH_PRESENCE":{"state":"RESOLVED","material":True,"reason":"BOUND_SOURCE_SHOWS_ACTIVE_NURSING_STUDENT_RESOURCE_AND_SHOP_PRESENCE"},
        }
    if candidate_key=="powered-by-yarn-and-chaos":
        return {
            "G3_CHANNELS_AND_PURCHASERS":{"state":"UNRESOLVED","material":None,"reason":"HANDBAG_BRAND_CHANNEL_OBSERVED_BUT PURCHASER_OVERLAP_NOT_EXHAUSTIVELY_PROVEN"},
            "G4_REGISTRANT_MARKETPLACE_OR_MERCH_PRESENCE":{"state":"RESOLVED","material":False,"reason":"BOUND_SOURCE_IDENTIFIES_CHAOS_BY_ELSIE_AS_HANDBAG_BRAND_AND_SHOPLC_RETAIL_PRESENCE"},
        }
    return {
        "G3_CHANNELS_AND_PURCHASERS":{"state":"UNRESOLVED","material":None,"reason":"NO_CANDIDATE_RULE"},
        "G4_REGISTRANT_MARKETPLACE_OR_MERCH_PRESENCE":{"state":"UNRESOLVED","material":None,"reason":"NO_CANDIDATE_RULE"},
    }
