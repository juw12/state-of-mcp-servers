import json
d = json.load(open("scan/scan_results.json", encoding="utf-8"))
print("scanned_at:", d["scanned_at"])
print("totals:", d["totals"])
print()
for r in d["results"]:
    real = r["findings_total"] - r.get("suppressed", 0)
    print(f"{r['repo']:24} files={r['files_scanned']:4}  total={r['findings_total']:4}  real={r['findings_real']:4}  high={r['high']}  med={r['medium']}  verdict={r['verdict']}")
    print("   rules:", dict(r["rules"]))
    print("   notable:", len(r.get("notable", [])))
