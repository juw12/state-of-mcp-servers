import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "scan_results.json")))
def safe(s, n=95):
    return "".join(c if 32 <= ord(c) < 127 else f"\\u{ord(c):04x}" for c in s)[:n]
for r in d["results"]:
    print(f"\n=== {r['repo']}  {r['verdict']}  (real={r['findings_real']}, high={r['high']}, med={r['medium']}) ===")
    shown = 0
    for f in r.get("notable", []):
        if f["severity"] == "high" and not f.get("likely_doc"):
            print(f"  [REAL-HIGH] {f['rule']}  {f['file']}:{f['line']}  {safe(f['snippet'])}")
            shown += 1
            if shown >= 14:
                print("   ..."); break
    doc_high = [f for f in r.get("notable", []) if f["severity"] == "high" and f.get("likely_doc")]
    if doc_high:
        print(f"  (suppressed-doc high: {len(doc_high)}) e.g. {doc_high[0]['rule']} {doc_high[0]['file']}")
