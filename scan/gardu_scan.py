#!/usr/bin/env python3
"""Gardu static scanner for public MCP servers + skills.

A compact, dependency-free port of the Hexbane rule philosophy (HB101-HB701),
run against cloned top public MCP servers and skills to produce a real
'state of MCP servers' security scan. Pattern/structure scanner: it reads
text only, does not execute code or follow URLs. PASS = 'nothing known found',
not 'safe'.
"""
import os, re, json, base64, hashlib

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repos")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next", "site", ".idea", ".vscode", "vendor", "target", ".pytest_cache", "egg-info"}
TEXT_EXT = {".md", ".markdown", ".txt", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".json", ".jsonc", ".json5", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".env", ".toml", ".sh", ".bash", ".zsh", ".ps1", ".cs", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".c", ".h", ".cpp", ".hpp", ".css", ".scss", ".html", ".htm", ".vue", ".svelte", ".proto", ".graphql", ".xml", ".svg", ".gradle", ".properties", ".tf", ".tfvars"}
MAX_BYTES = 2 * 1024 * 1024

HIDDEN = re.compile(
    "[\u200b\u200c\u200d\u2060\u00ad\u202a\u202b\u202c\u202d\u202e"
    "\u2061\u2062\u2063\u2064\ufeff"
    "\u180e\u034f\u061c\ufeff"
    "\U000e0000-\U000e007f]")  # unicode tag blocks (8-hex \U form)
BIDI = re.compile("[\u202a-\u202e\u2066-\u2069\ufdf0-\ufdfd]")
ZERO = re.compile("[\u200b\u200c\u200d\u2060\u00ad\u180e\u034f\u061c\u2061\u2062\u2063\u2064]")
TAGCHAR = re.compile("[\U000e0000-\U000e007f]")
HTML_COMMENT = re.compile(r"<!--(.{0,400}?)-->", re.S)
B64 = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")

INJECT = [
    # strong override patterns (high)
    ("HB201", re.compile(r"ignore (all )?(previous|prior|above|earlier) instructions", re.I)),
    ("HB205", re.compile(r"your (new|updated|revised|hidden|secret) instructions?", re.I)),
    ("HB206", re.compile(r"(system prompt|system message).{0,40}(reveal|leak|show|print)", re.I)),
    # weaker / advice-matching patterns (medium)
    ("HB202", re.compile(r"you (are now|must) (act|behave) as", re.I)),
    ("HB202", re.compile(r"from now on (you|act|ignore|disregard)", re.I)),
    ("HB203", re.compile(r"(do|don't|never) (not |)tell the user", re.I)),
    ("HB204", re.compile(r"without (telling|informing|letting) the user", re.I)),
]
SECRET = [
    ("HB301", re.compile(r"~/\.ssh|\\?\.ssh[/\\]|id_rsa|id_ed25519", re.I)),
    ("HB310", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("HB311", re.compile(r"ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")),
    ("HB311", re.compile(r"xox[bpars]-[A-Za-z0-9-]{10,}")),
    ("HB311", re.compile(r"sk-[A-Za-z0-9]{24,}")),
    ("HB311", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY")),
    ("HB310", re.compile(r"aws_secret_access_key|client_secret|api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9]{16,}", re.I)),
]
EXEC = [
    ("HB401", re.compile(r"curl[^\n|]{0,120}\|\s*(sudo\s+)?(ba|z)?sh\b")),
    ("HB401", re.compile(r"wget[^\n|]{0,120}\|\s*(sudo\s+)?(ba|z)?sh\b")),
    ("HB401", re.compile(r"iex\s*\(\s*\(?(iwr|invoke-webrequest)", re.I)),
    ("HB402", re.compile(r"(discord\.com/api/webhooks|api\.telegram\.org|hooks\.slack\.com/[A-Za-z0-9/-]+|pipedream\.net|requestbin\.com)", re.I)),
    ("HB402", re.compile(r"pastebin\.com/raw|ngrok\.(io|app|dev|top)")),
    ("HB403", re.compile(r"rm\s+-rf\s+(/|~|\$HOME|\*)")),
    ("HB405", re.compile(r"(crontab|schtasks|launchctl|systemctl enable|/etc/cron)", re.I)),
]
CFG = [
    ("HB501", re.compile(r"npx\s+(-[a-z]+\s+)*@[a-z0-9._/-]+(?!\s*@[0-9])", re.I)),   # npx pkg with no version pin
    ("HB501", re.compile(r"uvx\s+[a-z0-9._-]+(?!\s*==)", re.I)),
    ("HB505", re.compile(r"--privileged", re.I)),
    ("HB502", re.compile(r"['\"](sh|bash|zsh)\s+-c['\"]", re.I)),
]
PLAIN_HTTP = re.compile(r"['\"]http://(?!localhost|127\.0\.0\.1|example|0\.0\.0\.0)[a-z0-9.-]+", re.I)
SECRETPARAM = re.compile(r"[\"']?(api[_-]?key|secret|token|password|passwd|auth[_-]?token|bearer)[\"']?\s*[:=]", re.I)
LONGLINE = re.compile(r"^.{600,}$", re.M)

FAMILY = {"HB1":"Hidden content","HB2":"Injection","HB3":"Secrets","HB4":"Execution & exfiltration","HB5":"MCP config","HB6":"Tool manifest","HB7":"Scope"}
SEV = {}
SEVERITY = {
    # high = active-compromise indicator in live code
    "HB201": "high", "HB205": "high", "HB206": "high",  # strong prompt-injection override
    "HB301": "high", "HB311": "high",                     # ssh private-key refs / real token formats
    "HB402": "high",                                       # data-exfiltration endpoints
    # medium = risky pattern / hygiene
    "HB202": "medium", "HB203": "medium", "HB204": "medium",  # weaker injection / info-hiding
    "HB101": "medium", "HB103": "medium", "HB105": "medium",  # hidden content / base64 payload
    "HB310": "medium",                                     # key-id / env-var-name references
    "HB401": "medium", "HB403": "medium", "HB405": "medium",  # shell exec / persistence
    "HB501": "medium", "HB502": "medium", "HB503": "medium", "HB505": "medium",  # MCP config
}
def sev_of(rid):
    # HB6xx (secret-shaped tool params) is informational: pervasive in MCP tools, not a verdict signal.
    if rid.startswith("HB6"):
        return "low"
    return SEVERITY.get(rid, "medium")

PLACEHOLDER = re.compile(
    r"(x{3,}|your[_ -]|<[^<>]{2,}>|\{[^{}]{2,}\}|\$your|changeme|change_me|dummy|redacted|placeholder|\bexample\b|\bsample\b|\bfake\b|\btodo\b)", re.I)

def looks_like_doc(path, line, rule):
    """Heuristic: finding is likely documentation / a placeholder / an example, not a live finding."""
    base = os.path.basename(path).lower()
    sl = "/" + path.lower()              # slash-anchored so root-level dirs (test/, evals/) match too
    lname = line.lower()
    # A placeholder value is not a real finding.
    if PLACEHOLDER.search(line):
        return True
    # Doc / example / fixture / test / eval / scaffold files: the vector is documented or tested here by design.
    docfile = (
        base in ("readme.md", "readme.rst", "changelog.md", "news.md", "doc.md",
                 "docs.md", "license.md", "contributing.md", "faq.md", "code-of-conduct.md",
                 "quickstart.md", "getting-started.md")
        or any(x in sl for x in ("/docs/", "/doc/", "/test/", "/tests/", "/example/",
                                 "/examples/", "/fixture/", "/fixtures/", "/mock/",
                                 "/mocks/", "/sample/", "/samples/", "/spec/", "/snapshots/",
                                 "/eval/", "/evals/", "/eval-tests/", "/scaffold/"))
        or ".example" in base or ".sample" in base
        or base.startswith(("example", "sample", "fixture", "mock", "test_", "conftest", "eval_"))
        or base.endswith(("_test.go", ".test.ts", ".test.tsx", ".test.js", ".test.jsx",
                          ".test.mjs", ".test.py", ".spec.ts", ".spec.tsx", ".spec.js",
                          ".spec.jsx", ".spec.mjs", "_test.py", "_test.js", "_test.ts"))
        or "_test." in base
    )
    if docfile:
        return True
    # Prose (markdown/reST): secret / exec / config matches are examples, not live behavior.
    # Hidden content (HB1) and injection (HB2) stay live in prose - a skill IS its instructions.
    if base.endswith((".md", ".rst", ".adoc")) and not rule.startswith(("HB1", "HB2")):
        return True
    return False

def scan_file(path, root):
    findings = []
    try:
        st = os.lstat(path)
        if st.st_size == 0 or st.st_size > MAX_BYTES:
            return findings, "skipped-size"
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            text = f.read()
    except UnicodeDecodeError:
        return findings, "skipped-binary"
    except Exception:
        return findings, "skipped"
    rel = os.path.relpath(path, root).replace("\\", "/")
    lines = text.splitlines()

    def add(rid, line_no, snippet, note=""):
        findings.append({
            "rule": rid, "family": FAMILY.get(rid[:3], "Other"), "severity": sev_of(rid),
            "file": rel, "line": line_no, "snippet": snippet[:240], "note": note,
            "likely_doc": looks_like_doc(rel, snippet, rid),
        })

    # hidden content
    zw = ZERO.findall(text)
    tags = TAGCHAR.findall(text)
    bidi = BIDI.findall(text)
    if zw or tags or bidi:
        first = next((i+1 for i, l in enumerate(lines) if ZERO.search(l) or TAGCHAR.search(l) or BIDI.search(l)), 0)
        add("HB101", first, "".join(sorted(set(zw+tags+bidi)))[:40] + f"  (+{len(zw)+len(tags)+len(bidi)} hidden chars total)",
            f"zero-width={len(zw)} bidi={len(bidi)} tags={len(tags)}")
    # html comment with instruction-ish content
    for m in HTML_COMMENT.finditer(text):
        body = m.group(1)
        if re.search(r"ignore|instruction|system|secret|do not|exfiltrat|token|credential", body, re.I):
            ln = text.count("\n", 0, m.start()) + 1
            add("HB103", ln, body.strip()[:160], "instruction-laden HTML comment")
    # base64 blobs (possible payload) - only on smallish text to stay fast
    if len(text) < 500_000:
        for m in B64.finditer(text):
            s = m.group(0)
            if len(s) >= 80:  # only large blobs
                try:
                    dec = base64.b64decode(s + "=" * (-len(s) % 4), validate=False)
                    if re.search(rb"[a-zA-Z]{3,} [a-zA-Z]{3,} [a-zA-Z]{3,}|instruction|ignore|curl|http", dec):
                        ln = text.count("\n", 0, m.start()) + 1
                        add("HB105", ln, s[:40] + "... (decodes to text)", "base64 blob decodes to instruction-like text")
                        break
                except Exception:
                    pass
    # injection / secrets / exec
    for i, l in enumerate(lines, 1):
        if len(l) > 1500:  # skip minified/giant lines
            continue
        for rid, rx in INJECT:
            if rx.search(l):
                add(rid, i, l.strip())
        for rid, rx in SECRET:
            if rx.search(l):
                add(rid, i, l.strip())
        for rid, rx in EXEC:
            if rx.search(l):
                add(rid, i, l.strip())
        for rid, rx in CFG:
            if rx is not PLAIN_HTTP and rx.search(l):
                add(rid, i, l.strip())
        if PLAIN_HTTP.search(l):
            add("HB503", i, l.strip(), "plain-HTTP remote (no TLS)")
        if SECRETPARAM.search(l):
            add("HB602", i, l.strip(), "secret-shaped key/param")

    return findings, "ok"

def scan_repo(name):
    root = os.path.join(ROOT, name)
    if not os.path.isdir(root):
        return None
    nfiles = 0; ntext = 0; nbin = 0; nsize = 0
    findings = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for fn in fn:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in TEXT_EXT:
                continue
            p = os.path.join(dp, fn)
            nfiles += 1
            f, status = scan_file(p, root)
            if status == "ok":
                ntext += 1
            elif status == "skipped-binary":
                nbin += 1
            elif status == "skipped-size":
                nsize += 1
            findings.extend(f)
    # verdict
    real = [f for f in findings if not f["likely_doc"]]
    hi = [f for f in real if f["severity"] in ("high",)]
    md = [f for f in real if f["severity"] == "medium"]
    if hi:
        verdict = "FAIL"
    elif md:
        verdict = "REVIEW"
    else:
        verdict = "PASS"
    rule_counts = {}
    for f in findings:
        rule_counts[f["rule"]] = rule_counts.get(f["rule"], 0) + 1
    return {
        "repo": name, "files_total": nfiles, "files_scanned": ntext,
        "files_binary_skipped": nbin, "files_size_skipped": nsize,
        "findings_total": len(findings),
        "findings_real": len(real), "high": len(hi), "medium": len(md),
        "verdict": verdict, "rules": rule_counts,
        "notable": sorted([f for f in real if f["severity"] in ("high", "medium")], key=lambda x: ({"high": 0, "medium": 1}.get(x["severity"], 2), x["file"]))[:30],
    }

def main():
    repos = sorted([d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d)) and not d.startswith(".")])
    results = [r for r in (scan_repo(x) for x in repos) if r]
    tot = {
        "repos": len(results),
        "files_scanned": sum(r["files_scanned"] for r in results),
        "files_total": sum(r["files_total"] for r in results),
        "findings_total": sum(r["findings_total"] for r in results),
        "verdicts": {v: sum(1 for r in results if r["verdict"] == v) for v in ("PASS", "REVIEW", "FAIL")},
        "rules": {},
    }
    for r in results:
        for k, v in r["rules"].items():
            tot["rules"][k] = tot["rules"].get(k, 0) + v
    out = {"scanned_at": "2026-11-10", "results": results, "totals": tot}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    for r in results:
        print(f"{r['repo']:<24} {r['verdict']:<7} files={r['files_scanned']:<5} findings={r['findings_total']:<5} real={r['findings_real']:<4} rules={r['rules']}")
    print("TOTALS", tot["verdicts"], "files", tot["files_scanned"], "findings", tot["findings_total"])
    print("saved scan_results.json")

if __name__ == "__main__":
    main()
