#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

SERIAL="90319838"
MARK="NURSING SCHOOL JEWELS"
SHARED_COMPONENT="NURSING SCHOOL"
URL=f"https://tsdr.uspto.gov/#caseNumber={SERIAL}&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch"


def compact(value):
    return re.sub(r"\s+"," ",value or "").strip()


def body_text(page):
    try:
        return compact(page.locator("body").inner_text(timeout=5000))
    except Exception:
        return ""


def visible_mark_info_controls(page):
    controls=[]
    for selector in ["button","a","[role='button']"]:
        try:
            loc=page.locator(selector)
            for i in range(min(loc.count(),300)):
                el=loc.nth(i)
                if not el.is_visible():
                    continue
                txt=compact(el.inner_text(timeout=1000))
                if "mark information" in txt.lower():
                    controls.append({
                        "selector":selector,
                        "index":i,
                        "text":txt[:200],
                        "aria_expanded":el.get_attribute("aria-expanded"),
                        "aria_controls":el.get_attribute("aria-controls"),
                        "href":el.get_attribute("href"),
                    })
        except Exception:
            pass
    return controls


def main():
    out={
        "schema":"AVER_TSDR_MARK_INFO_CANARY",
        "official_source":True,
        "known_identifier_only":True,
        "serial":SERIAL,
        "mark":MARK,
        "shared_component":SHARED_COMPONENT,
        "candidate_breadth_expanded":False,
        "tm_decision_authorized":False,
        "daily7_live_gate_authorized":False,
        "phase_state":"TSDR_MARK_INFO_PARTIAL",
        "state":"UNPROVEN",
        "failure_signature":None,
    }
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable:
            launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        page=browser.new_page(viewport={"width":1440,"height":1200})
        try:
            page.goto(URL,wait_until="domcontentloaded",timeout=30000)
            base=""
            for _ in range(30):
                page.wait_for_timeout(500)
                base=body_text(page)
                if SERIAL in base and MARK.lower() in base.lower():
                    break
                if "system was unable to perform your search" in base.lower():
                    break
            out["base_record_bound"]=SERIAL in base and MARK.lower() in base.lower()
            out["base_body_excerpt"]=base[:3500]
            if not out["base_record_bound"]:
                out["failure_signature"]="TSDR_BASE_RECORD_NOT_BOUND"
            else:
                controls=visible_mark_info_controls(page)
                out["mark_info_controls"]=controls
                clicked=False
                click_error=None
                for control in controls:
                    try:
                        el=page.locator(control["selector"]).nth(control["index"])
                        el.click(timeout=3000)
                        clicked=True
                        page.wait_for_timeout(700)
                        break
                    except Exception as exc:
                        click_error=f"{type(exc).__name__}:{str(exc)[:180]}"
                out["mark_info_clicked"]=clicked
                out["mark_info_click_error"]=click_error
                expanded=body_text(page)
                lower=expanded.lower()
                out["expanded_body_excerpt"]=expanded[:6500]
                idx=lower.find("disclaim")
                disclaimer_context=expanded[max(0,idx-250):idx+1200] if idx>=0 else None
                out["disclaimer_context"]=disclaimer_context
                out["disclaimer_marker_seen"]=idx>=0
                out["shared_component_in_disclaimer_context"]=bool(disclaimer_context and SHARED_COMPONENT.lower() in disclaimer_context.lower())
                out["component_strength_signal"]="DISCLAIMED_COMPONENT" if out["shared_component_in_disclaimer_context"] else "UNRESOLVED"
                if clicked and out["disclaimer_marker_seen"] and out["shared_component_in_disclaimer_context"]:
                    out["state"]="PASS"
                    out["phase_state"]="TSDR_MARK_INFO_DISCLAIMER_PASS"
                elif not clicked:
                    out["failure_signature"]="TSDR_MARK_INFO_CONTROL_NOT_CLICKED"
                else:
                    out["failure_signature"]="TSDR_DISCLAIMER_NOT_MACHINE_BOUND"
        except Exception as exc:
            out["state"]="BLOCKED"
            out["failure_signature"]=f"{type(exc).__name__}:{str(exc)[:220]}"
        finally:
            page.close(); browser.close()
    path=Path("artifacts/tsdr-mark-info"); path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"],"state=",out["state"],"failure=",out.get("failure_signature"))
    if out["phase_state"]!="TSDR_MARK_INFO_DISCLAIMER_PASS":
        raise SystemExit("TSDR_MARK_INFO_DISCLAIMER_NOT_PASS")

if __name__=="__main__":
    main()
