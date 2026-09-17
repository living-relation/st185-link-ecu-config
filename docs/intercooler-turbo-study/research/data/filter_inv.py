import re, os
OUT = r"C:\Users\danie\AppData\Roaming\Claude\local-agent-mode-sessions\1cec9723-b110-46f1-9694-4a2692e2397f\a8dc0527-c42c-4163-8eb6-e49e1c4c8497\local_e957a84a-65a7-425d-93d0-0e485ed7f050\outputs"
txt = open(os.path.join(OUT, "invoices_ocr.txt"), encoding="utf-8").read()
blocks = txt.split("========== ")
KEY = r"(turbo|inject|intercool|charge|manifold|wastegate|waste gate|bov|blow.?off|radiator|pipe|piping|coupler|clamp|pump|fuel|ethanol|e85|cam|piston|rod|head gasket|throttle|maf|map sensor|iat|boost|gt28|gt30|gt35|gtx|efr|g25|g30|g35|precision|garrett|borgwarner|downpipe|elbow|silicone|oil cooler|thermostat|hose|filter|regulator|rail|spark|coil|clutch|flywheel|valve|port|billet|bare core|core)"
for b in blocks[1:]:
    name, _, body = b.partition("==========")
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    hits = [l for l in lines if re.search(KEY, l, re.I) and len(l) > 8]
    if hits:
        print("\n### " + name.strip())
        seen = set()
        for h in hits:
            if h not in seen:
                seen.add(h)
                print("  " + h[:160])
