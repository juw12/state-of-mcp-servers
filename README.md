# Gardu — The State of MCP Servers

> **Breaks the hex before your AI agent falls for it.**
> A public security scan of the top MCP servers and skills — who ships them, how big they
> are, and what a static security scan finds **before** your AI agent trusts them.

This is a **Gardu** report. Gardu is the scan engine behind
[Hexbane](https://juw12.github.io/hexbane/) — a free, dependency-free static scanner for
the AI-agent surface: MCP servers, agent skills, and tool manifests.

![Desktop (dark)](docs/screenshots/gardu-desktop-dark.png)

<details>
<summary><strong>Light theme</strong></summary>
<br>
![Desktop (light)](docs/screenshots/gardu-desktop-light.png)
</details>

<details>
<summary><strong>Mobile</strong></summary>
<br>
![Phone](docs/screenshots/gardu-phone-dark.png)
</details>

---

## What this is

The Model Context Protocol lets an AI agent get *hands* — file system, browser, shell,
databases, cloud APIs. Power in a third-party plugin is a supply-chain attack surface.
This report:

1. **Catalogs the ecosystem** — ~359,500 public GitHub repos match `mcp` in their name;
   45 of the top servers and 7 of the top skill collections are tracked with live
   star/fork/language data.
2. **Scans the top of the distribution** — the 7 most-starred cloneable servers + the
   Anthropic skills repo (2,952 files) were run through the Gardu static scanner.
3. **States the state** — what the scan actually finds, what those findings mean, and what
   you should do about it.

### The headline

> **Across all 7 top servers, Gardu found 0 real high-severity findings — no active
> compromise in live code.** Every repo lands at **REVIEW**, not PASS: powerful,
> third-party tools that can run commands and hold your credentials, shipping no statement
> of what they'll do with that power. That is the gap Gardu closes.

The recurring findings are hygiene and by-design capability — secret-shaped tool
parameters, key-id/env-var references, plain-HTTP endpoints, unpinned `npx`, and
exec-capability (concentrated in the shell-by-design DesktopCommanderMCP) — not malice.

Read the full analysis in [`report/state-of-mcp-servers.md`](report/state-of-mcp-servers.md).

---

## Open it

- **Live:** `https://juw12.github.io/<this-repo>/` (GitHub Pages, auto-deployed from `web/`)
- **Local:** open [`web/index.html`](web/index.html) in a browser, or
  `python -m http.server` from `web/` and visit `http://localhost:8000`.
- The page is a single interactive landing page — no build step, no dependencies,
  light + dark theme. All numbers are generated from `web/data.js`, not hand-typed.

---

## Reproduce the scan

The scanner is pure Python stdlib. No API keys, no network, no telemetry.

```bash
# clone any MCP server / skills repo
git clone --depth 1 https://github.com/<owner>/<server>.git

# from this repo's scan/ folder, point it at your clones (scan/repos/) and run:
python scan/gardu_scan.py
# -> writes scan/scan_results.json with per-file findings, severities, and a verdict
#    (PASS / REVIEW / FAIL) per repo
```

Rebuild the report data + page bundle:

```bash
python scan/build_data.py      # GitHub API meta  -> data/servers.json, skills.json, ecosystem.json
python scan/make_webdata.py    # data/*.json      -> web/data.js (window.MCPDATA)
```

---

## What Gardu checks

Hexbane-style rule families, per line, over every text file:

| Family | Checks |
|---|---|
| **HB1xx** | hidden content — zero-width / bidi / PUA unicode, hidden tag text, base64 payloads (decoded before judging) |
| **HB2xx** | prompt injection — instruction-override phrases ("ignore all previous instructions", "reveal your system prompt") |
| **HB3xx** | secrets — private keys, GitHub/Anthropic token formats, key-id / env-var references |
| **HB4xx** | execution & exfil — shell/exec, remote HTTP, plain `http://` (non-TLS), persistence |
| **HB5xx** | MCP-config hygiene — unpinned `npx`, remote transports, credential paths |
| **HB6xx** | tool manifest — secret-shaped tool parameters (informational) |

**Severity discipline:** only a genuine, high-severity, **non-document** finding can force
a `FAIL`. Attack patterns that appear in docs/tests/examples/fixtures are suppressed — a
vector *documented or tested* in a repo is expected (that's how security tooling is
written). Injection + hidden-content detection stays **live in `.md`**, because a skill *is*
its instructions.

**Honest limits:** static analysis only — no code execution, no dependency/URL following.
Doc/test suppression cuts both ways (a malicious payload shipped inside a `test_*` file is
under-counted). A 7-of-~359,500 sample, not a census. Point-in-time.

---

## Repo layout

```
web/                      # the landing page (GitHub Pages root)
  index.html  styles.css  app.js  data.js  favicon.svg
  data/                   # downloadable raw JSON (servers, skills, scan, ecosystem)
scan/
  gardu_scan.py           # the scanner (pure stdlib)
  build_data.py           # GitHub API -> data/*.json
  make_webdata.py         # data/*.json -> web/data.js
  fetch_meta*.py          # GitHub API meta fetchers
  scan_results.json       # last scan output
data/                     # generated datasets
report/
  state-of-mcp-servers.md # the full report
docs/screenshots/         # light + dark + mobile
.github/workflows/pages.yml
```

---

## License

MIT. Gardu is part of the Hexbane scanner family. Not a security audit; a scanner.
**PASS = nothing known found, not "safe".**
