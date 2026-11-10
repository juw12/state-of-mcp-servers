# The State of Public MCP Servers — a Gardu scan

**Gardu · security scanner for AI-agent skills & MCP servers** · scanned **2026-11-10**

> *Breaks the hex before your AI agent falls for it.*
> Gardu is the scan engine behind [Hexbane](https://juw12.github.io/hexbane/) — a static
> security scanner for the growing surface of Model Context Protocol (MCP) servers and
> agent skills. This report is the first public "state" snapshot: what the most popular
> MCP servers and skills look like under a security lens, before you hand them your agent.

---

## 1. The scale of the problem

The Model Context Protocol has become the de-facto way to give an AI agent hands — file
system access, browser control, shell, databases, cloud APIs. That is power, and power in
a third-party plugin is a supply-chain attack surface.

- **≈ 359,500** public GitHub repositories currently match `mcp` in their name.
  (A broad upper bound — the name-matched set, not a deduped count of servers — but it
  shows the pace at which this surface is exploding.)
- **45** of the top MCP servers and **7** of the top agent-skill collections were
  cataloged for this report, with live star/fork/language data from the GitHub API.
- The top of the distribution is dominated by well-known orgs: `n8n`, `anthropics`,
  `modelcontextprotocol`, `ChromeDevTools`, `run-llama`, `microsoft`, `github`,
  `Cloudflare`, `mongodb`.

**The uncomfortable part:** almost none of these ship a security attestation, a signed
manifest, or a "what this server can do" card. You load it, and you inherit whatever it
does. Gardu exists to run *before* you do.

---

## 2. How we scanned (methodology)

We cloned the **7 most-starred cloneable** public MCP servers / skill repos and ran the
**Gardu static scanner** — the same rule engine as Hexbane — over every source file.

| Repo | Owner | Files scanned | Findings | Real* | High | Verdict |
|---|---|---:|---:|---:|---:|---|
| modelcontextprotocol/servers | modelcontextprotocol | 364 | 146 | 14 | 0 | **REVIEW** |
| anthropics/skills | anthropics | 270 | 223 | 96 | 0 | **REVIEW** |
| github/github-mcp-server | github | 403 | 273 | 47 | 0 | **REVIEW** |
| wonderwhy-er/DesktopCommanderMCP | wonderwhy-er | 638 | 337 | 84 | 0 | **REVIEW** |
| geelen/mcp-remote | geelen | 63 | 257 | 35 | 0 | **REVIEW** |
| Cloudflare/mcp-server-cloudflare | Cloudflare | 422 | 564 | 341 | 0 | **REVIEW** |
| mongodb-js/mongodb-mcp-server | mongodb-js | 792 | 646 | 237 | 0 | **REVIEW** |
| **Total** | | **2,952** | **2,446** | **874** | **0** | |

\* "Real" = findings **not** suppressed as documentation/test/fixture. The full finding
count (2,446) includes informational hits that live in docs and test scaffolds.

**What Gardu checks** (rule families, Hexbane-style):
- **HB1xx — hidden content:** zero-width / bidi-override / PUA characters, tag-like
  control text, hidden base64 payloads (decoded before judging).
- **HB2xx — prompt injection:** instruction-override phrases ("ignore all previous
  instructions", "your new secret instructions", "reveal your system prompt").
- **HB3xx — secrets:** private keys, GitHub/Anthropic-format tokens, `.env` handling,
  key-id / env-var-name references.
- **HB4xx — execution & exfil:** shell/exec calls, remote HTTP endpoints, non-TLS
  (plain `http://`) traffic, persistence hooks.
- **HB5xx — MCP-config hygiene:** unpinned `npx`, remote transports, credential paths.
- **HB6xx — tool manifest:** secret-shaped tool parameters (informational).

**Severity discipline.** Not every hit is a threat. Gardu scores each finding and only a
**genuine, high-severity, non-document** finding can force a `FAIL`. Crucially, the
scanner separates **live code** from **docs / tests / examples / fixtures** — a malicious
pattern *documented or tested* in a repo is expected (that's how security tooling is
written), so it is not counted as an active compromise. The scanner deliberately keeps
injection and hidden-content detection **live in `.md`**, because an agent skill *is* its
instructions — a malicious skill would still be caught.

---

## 3. The headline result

> **Across all 7 top MCP servers / skill repos, Gardu found 0 real high-severity
> findings — no active-compromise indicator (no injected payload, no leaked private key,
> no exfiltration endpoint) in live code.**

Every repo lands at **REVIEW**, not PASS. That is a deliberate, principled stance:
Gardu never auto-trusts a third-party server. `PASS` would mean "clean enough to load
without a second look"; `REVIEW` means "no red flags, but it still touches your machine —
you should know what it can do." A handful of the most popular servers on the planet earn
REVIEW, not PASS, and that is exactly the right answer.

So what *are* the findings? They are overwhelmingly **hygiene and by-design capability**,
not malice:

| Rule | What it is | Count | Read |
|---|---|---:|---|
| HB602 | secret-shaped tool parameters | 1,821 | Informational. MCP tools *legitimately* take keys, tokens and connection strings as parameters. Not a leak. |
| HB310 | key-id / env-var-name references | 251 | The server needs credentials to do its job (DB user, OAuth client, etc.). Review how they're handled. |
| HB503 | plain-HTTP (non-TLS) endpoints | 197 | Some referenced URLs are not `https`. Worth tightening. |
| HB501 | unpinned `npx` | 98 | Supply-chain hygiene — pin the package version you launch. |
| HB401 / HB403 / HB405 | exec / remote / persistence | 29 | Concentrated in **DesktopCommanderMCP**, which is a remote *shell by design* — double-edged, not malicious. |
| HB311 | real token/private-key *format* | 25 | All matched **placeholder values** in test fixtures (`ghp_xxx…`), verified by hand — no real secrets. |
| HB101 | hidden unicode | 5 | Minor artifacts; one stray `\u200d` in DCMCP live code. |
| HB402 | exfiltration endpoint | 2 | Both in an **eval/test script** (ngrok for local dev), not live exfil. |

**The recurring signal is not "these servers are compromised."** It is: *these are
powerful, third-party tools that can run commands, reach the network, and hold your
credentials — and they ship no statement of what they'll do with that power.* That is the
gap Gardu fills.

### Per-repo, what's actually notable

- **modelcontextprotocol/servers** — the official reference implementations are the
  cleanest. Findings are a README example using unpinned `npx -y @modelcontextprotocol/…`
  and a couple of env-var refs. Textbook hygiene.
- **anthropics/skills** — a large collection of `SKILL.md` instruction files. The 94
  medium findings are mostly MCP-config hygiene and non-TLS example URLs inside the skill
  docs. No injection found in any skill.
- **github/github-mcp-server** — 21 token-*format* hits, all `ghp_xxx` placeholders in
  `*_test.go`; 6 real key-id/env refs. The one injection-pattern match sits in a doc and
  is suppressed. Clean in live code.
- **DesktopCommanderMCP** — the one to understand before you load. It is a **desktop
  shell**: 12 exec + 7 remote-http + 6 persistence findings are the *product*, not a bug.
  It also has 3 hidden-unicode artifacts (one a stray `\u200d` in live code). Powerful and
  legitimate — but it should be the *last* server you auto-load, and only on a machine you
  trust.
- **geelen/mcp-remote** — a proxy/bridge that shuttles OAuth tokens between clients and
  remote servers. 52 key-id/env refs and 6 plain-http hits are expected for a token broker.
- **Cloudflare/mcp-server-cloudflare** — 9 unpinned-`npx` + 85 key-id refs + 20 plain-http.
  Standard for a cloud control-plane server; pin the version and review the credential path.
- **mongodb-js/mongodb-mcp-server** — 97 key-id/env refs (it connects to your databases —
  of course it needs the connection string). The 4 private-key-format hits are in `.test.ts`
  fixtures and the 2 "exfil" hits are in an eval script. Clean in live code.

---

## 4. Six observations on the state of the ecosystem

1. **The surface is huge and young.** ~359,500 name-matched repos; the top of the
   distribution is real, well-known orgs, but the long tail is unvetted by anyone.
2. **Category spread.** Official/SDK, Code & Dev tools, and Browser & Web are the densest
   categories — the three that touch your files, your code, and your credentials.
3. **The big servers are not compromised — they're just powerful.** 0 active-compromise
   indicators in the 7 scanned. The medium findings are capability + hygiene, not malice.
4. **Skills are the bigger, faster-moving injection surface.** A skill *is* instructions to
   an LLM; a malicious skill needs no code at all. Skill collections (e.g. `anthropics/skills`)
   are large and heterogeneous, and none carry a trust signal. This is where injection risk
   concentrates.
5. **Almost nobody ships a security attestation.** None of the 7 publish "what this server
   can do and won't do." Gardu/Hexbane scans *before* you load, to close that gap.
6. **Plain-HTTP and unpinned launches are the quiet defaults.** 197 non-TLS endpoints and
   98 unpinned `npx` across just 7 repos — multiply that across the long tail and the
   supply-chain attack surface is large.

---

## 5. What you should do

- **Pin versions.** Never `npx -y <pkg>` an MCP server unpinned in production.
- **Prefer official / vendor servers.** The reference implementations scanned cleanest.
- **Gate remote HTTP.** Require `https`; flag any server that phones home over plain `http`.
- **Treat exec-capable servers as admin.** DesktopCommanderMCP and similar should be
  isolated, least-privilege, and on a machine you trust — not your daily driver.
- **Read skills as code.** A skill is an instruction-injection vector by definition.
- **Run a scanner before you load.** That's what this is for:
  `git clone` a repo, `python scan/gardu_scan.py`, read the verdict.

---

## 6. Honest caveats

- **Static analysis only.** Gardu does not execute code. It cannot catch runtime
  behavior, payloads built at runtime, or a *dependency* that is compromised upstream.
- **A sample, not a census.** 7 of ~359,500 name-matched repos were scanned — the
  highest-starred cloneable ones. The long tail is unmeasured here.
- **Doc/test suppression cuts both ways.** We suppress attack patterns that appear in
  docs/tests/examples (they're expected there). That reduces false positives, but it means
  a malicious payload shipped *inside* a file named `test_*` would be under-counted.
- **Stars ≠ safety.** Popularity is a proxy for attention, not for security review.
- **Point-in-time.** Verdicts reflect the commit cloned on 2026-11-10; repos move.

---

## Reproduce

```bash
# clone a server, scan it
git clone --depth 1 https://github.com/<owner>/<server>.git
# from the scan/ folder of this repo:
python gardu_scan.py          # writes scan_results.json with per-file findings + verdict
```

The interactive landing page renders this report live from `web/data.js` (all numbers
above are generated, not hand-typed).

*Gardu — part of the Hexbane scanner family. MIT-licensed. No API keys, no network calls,
no telemetry.*
