#!/usr/bin/env python3
from aver.production import live_class016_query, distinctive_live_class016_query

q='CM:"ANXIETY IS MY"'
assert live_class016_query(q) == 'CM:"ANXIETY IS MY" AND LD:true AND IC:016'
q2='CM:(/.*anxiety.*/ AND /.*is.*/ AND /.*my.*/)'
assert live_class016_query(q2) == 'CM:(/.*anxiety.*/ AND /.*is.*/ AND /.*my.*/) AND LD:true AND IC:016'
assert distinctive_live_class016_query("ANXIETY IS MY CARDIO") == "CM:(/.*anxiety.*/ AND /.*cardio.*/) AND LD:true AND IC:016"
print("AVER_HOLD_CALIBRATION_CLASS016_QUERY_TEST_PASS")
