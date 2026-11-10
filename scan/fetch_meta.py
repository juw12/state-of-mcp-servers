#!/usr/bin/env python3
"""Fetch real GitHub metadata for top public MCP servers + skills (stdlib only)."""
import json, urllib.request, urllib.parse, time, sys, os

API = "https://api.github.com"
HDRS = {"User-Agent": "gardu-mcp-state", "Accept": "application/vnd.github+json"}

def get(url):
    req = urllib.request.Request(url, headers=HDRS)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode()), r.status
    except Exception as e:
        return {"_err": str(e)}, 0

# Curated canonical set (top public MCP servers + skills). Stars verified live.
SERVERS = [
    "modelcontextprotocol/servers",
    "github/github-mcp-server",
    "modelcontextprotocol/inspector",
    "modelcontextprotocol/python-sdk",
    "modelcontextprotocol/typescript-sdk",
    "punkpeye/mcp-get",
    "punkpeye/awesome-mcp-servers",
    "geelen/mcp-remote",
    "wonderwhy-er/DesktopCommanderMCP",
    "composio-dev/composio",
    "supabase/supabase-mcp",
    "mongodb-js/mongodb-mcp-server",
    "Cloudflare/mcp-server-cloudflare",
    "browsermcp/mcp-serve",
    "microsoft/playwright-mcp",
    "firebase/firebase-tools",
    "n8n-io/n8n",
    "mcp-use/mcp-use",
    "seratch/mcp_grocery",
    "glama-ai/mcp-servers",
    "smithery-ai/smithery",
    "modelcontextprotocol/go-sdk",
    "run-llama/llama_index",
    "getmetal/metal-mcp",
    "metarank/mcp-server",
]
SKILLS = [
    "anthropics/skills",
    "anthropics/claude-code",
    "anthropics/claude-cookbooks",
    "obra/superpowers",
    "davila7/claude-code-templates",
    "hesreallyhim/awesome-claude-code",
    "wshobson/agents",
    "anthropics/anthropic-cookbook",
]

def norm(r):
    if not r or "_err" in r:
        return None
    return {
        "full_name": r.get("full_name"),
        "name": r.get("name"),
        "owner": (r.get("owner") or {}).get("login"),
        "stars": r.get("stargazers_count"),
        "forks": r.get("forks_count"),
        "desc": (r.get("description") or "").strip(),
        "lang": r.get("language"),
        "pushed": r.get("pushed_at"),
        "created": r.get("created_at"),
        "archived": r.get("archived", False),
        "topics": r.get("topics", []),
        "homepage": r.get("homepage"),
        "open_issues": r.get("open_issues_count"),
    }

out = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "servers": [], "skills": [], "search_top": []}
rate_left = None

def fetch_repo(fn):
    url = f"{API}/repos/{fn}"
    r, st = get(url)
    if "_err" not in r:
        rl = r.headers.get("X-RateLimit-Remaining") if hasattr(r, "headers") else None
    n = norm(r)
    if n:
        (out["servers"] if fn in SERVERS else out["skills"]).append(n)
    time.sleep(0.4)
    return n

for fn in SERVERS:
    n = fetch_repo(fn)
    print("server", fn, n["stars"] if n else "MISSING", flush=True)
for fn in SKILLS:
    n = fetch_repo(fn)
    print("skill", fn, n["stars"] if n else "MISSING", flush=True)

# One search: top MCP repos by stars (ecosystem scale)
q = urllib.parse.quote("mcp in:name,description,readme")
r, st = get(f"{API}/search/repositories?q={q}&sort=stars&order=desc&per_page=30")
if isinstance(r, dict) and "items" in r:
    out["search_total"] = r.get("total_count")
    for it in r["items"]:
        out["search_top"].append(norm(it))

os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "meta_raw.json"), "w") as f:
    json.dump(out, f, indent=2)
print("TOTAL search results:", out.get("search_total"))
print("saved meta_raw.json")
