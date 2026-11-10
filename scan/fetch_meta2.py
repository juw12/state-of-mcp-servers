#!/usr/bin/env python3
"""Complete the MCP metadata: corrected repo names + ecosystem-scale search. Stdlib only."""
import json, urllib.request, urllib.parse, time, os

API = "https://api.github.com"
HDRS = {"User-Agent": "gardu-mcp-state", "Accept": "application/vnd.github+json"}
HERE = os.path.dirname(os.path.abspath(__file__))

def get(url):
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())

def norm(r):
    if not r or "full_name" not in r:
        return None
    return {
        "full_name": r.get("full_name"), "name": r.get("name"),
        "owner": (r.get("owner") or {}).get("login"),
        "stars": r.get("stargazers_count"), "forks": r.get("forks_count"),
        "desc": (r.get("description") or "").strip(), "lang": r.get("language"),
        "pushed": r.get("pushed_at"), "created": r.get("created_at"),
        "archived": r.get("archived", False), "topics": r.get("topics", []),
        "homepage": r.get("homepage"), "open_issues": r.get("open_issues_count"),
    }

# Verified earlier this run (real star counts from api.github.com)
BASE = {
 "modelcontextprotocol/servers":91903,"github/github-mcp-server":34361,
 "modelcontextprotocol/inspector":11268,"modelcontextprotocol/python-sdk":24819,
 "modelcontextprotocol/typescript-sdk":13741,"punkpeye/awesome-mcp-servers":97557,
 "geelen/mcp-remote":1667,"wonderwhy-er/DesktopCommanderMCP":10278,
 "mongodb-js/mongodb-mcp-server":1160,"Cloudflare/mcp-server-cloudflare":4456,
 "microsoft/playwright-mcp":39405,"firebase/firebase-tools":4489,"n8n-io/n8n":209991,
 "mcp-use/mcp-use":10862,"modelcontextprotocol/go-sdk":5330,"run-llama/llama_index":52867,
 "anthropics/skills":191779,"anthropics/claude-code":155160,
}

# Corrected / renamed repos to fetch fresh
TO_FETCH = [
 "punkpeye/mcp-get","browsermcp/mcp-serve","supabase-community/supabase-mcp",
 "ComposioHQ/composio","anthropics/anthropic-cookbook","obra/superpowers",
 "davila7/claude-code-templates","hesreallyhim/awesome-claude-code","wshobson/agents",
 "modelcontextprotocol/registry","modelcontextprotocol/modelcontextprotocol",
]

meta = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "servers": {}, "skills": {}, "search_total": None, "search_top": []}

# seed base stars
for fn, s in BASE.items():
    bucket = meta["skills"] if fn.startswith("anthropics/") else meta["servers"]
    bucket[fn] = {"full_name": fn, "name": fn.split("/")[-1], "owner": fn.split("/")[0],
                  "stars": s, "desc": "", "lang": None, "pushed": None, "topics": []}

for fn in TO_FETCH:
    try:
        r = get(f"{API}/repos/{fn}")
        n = norm(r)
        if n:
            bucket = meta["skills"] if fn.startswith("anthropics/") else meta["servers"]
            bucket[fn] = n
            print("fetched", fn, n["stars"], flush=True)
        else:
            print("MISS", fn, flush=True)
    except Exception as e:
        print("ERR", fn, e, flush=True)
    time.sleep(0.3)

# ecosystem scale
for q in ["mcp in:name", "mcp server in:description,readme"]:
    try:
        r = get(f"{API}/search/repositories?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page=30")
        if meta["search_total"] is None:
            meta["search_total"] = r.get("total_count")
        for it in r["items"][:30]:
            meta["search_top"].append(norm(it))
        print("search", q, "total", r.get("total_count"), flush=True)
    except Exception as e:
        print("search err", q, e, flush=True)
    time.sleep(0.5)

with open(os.path.join(HERE, "meta_raw.json"), "w") as f:
    json.dump(meta, f, indent=2)
print("SERVERS", len(meta["servers"]), "SKILLS", len(meta["skills"]), "search_total", meta["search_total"])
print("saved meta_raw.json")
