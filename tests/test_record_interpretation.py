#!/usr/bin/env python3
from aver.record_interpretation import bind_record_anchor

NURSING = """Mark Details Status Class/Description NURSING SCHOOL IN A BOX ItsaCallingEducation, LLC 88404614 26 Apr 2019 Live/Registered on 19 Jul 2022 Consulting services about education Class 041 FIND NURSING SCHOOLS ORBIS EDUCATION SERVICES, LLC 86503335 14 Jan 2015 Live/Registered on 11 Feb 2026 Educational services Class 042 NURSING SCHOOL JEWELS Nursing School Jewels LLC 90319838 14 Nov 2020 Live/Registered on 31 Aug 2021 Notebooks; Flash cards; Notebook covers; Notebook dividers; printed educational materials; stickers Class 016 LITTLE NURSING SCHOOL LMS FRANCHISE SYSTEMS, LLC 86197868 19 Feb 2014 Live/Registered on 01 Nov 2024 Entertainment and educational services Class 041"""

YARN = """Mark Details Status Class/Description CHAOS BY ELSIE Shop LC Global Inc 90072046 24 Jul 2020 Live/Registered on 22 Jun 2021 Handbags Class 018 POWERED BY P PRAGMATIC SEMICONDUCTOR LIMITED 79424150 24 Mar 2025 Live/Registered on 21 Apr 2026 Electronic components Class 007 Class 009 POWERED BY : P RingIt, Inc. 98505468 17 Apr 2024 Live/Registered on 01 Apr 2025 Software as a service Class 009 Class 035"""

n = bind_record_anchor(NURSING, "NURSING SCHOOL JEWELS", "90319838", "016")
assert n["bound"] is True
assert n["identifier"] == "90319838"
assert "016" in n["classes"]
assert n["status"].lower().startswith("live/registered")

n_wrong = bind_record_anchor(NURSING, "NURSING SCHOOL JEWELS", "90319838", "025")
assert n_wrong["bound"] is False
assert n_wrong["failure_signature"] == "EXPECTED_CLASS_NOT_BOUND"

y = bind_record_anchor(YARN, "CHAOS BY ELSIE", "90072046", "018")
assert y["bound"] is True
assert y["identifier"] == "90072046"
assert "018" in y["classes"]

missing = bind_record_anchor(YARN, "POWERED BY YARN AND CHAOS", "90072046", "018")
assert missing["bound"] is False
assert missing["failure_signature"] == "MARK_NOT_BOUND_TO_SERIAL"

print("AVER_RECORD_INTERPRETATION_TEST_PASS")
