#!/usr/bin/env python3
"""Build clean, categorized datasets for the State of MCP Servers report.
Reads meta_raw.json (live GitHub data), dedupes, categorizes, writes data/*.json.
"""
import json, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
meta = json.load(open(os.path.join(HERE, "meta_raw.json")))

# repo dir name -> full_name for the 7 repos we actually scanned
SCANNED_DIRS = {
    "servers": "modelcontextprotocol/servers",
    "skills": "anthropics/skills",
    "github-mcp-server": "github/github-mcp-server",
    "DesktopCommanderMCP": "wonderwhy-er/DesktopCommanderMCP",
    "mcp-remote": "geelen/mcp-remote",
    "mcp-server-cloudflare": "Cloudflare/mcp-server-cloudflare",
    "mongodb-mcp-server": "mongodb-js/mongodb-mcp-server",
}
SCANNED_FULL = set(SCANNED_DIRS.values())

CAT = {
 "modelcontextprotocol/servers":"Official & SDK","modelcontextprotocol/inspector":"Official & SDK",
 "modelcontextprotocol/python-sdk":"Official & SDK","modelcontextprotocol/typescript-sdk":"Official & SDK",
 "modelcontextprotocol/go-sdk":"Official & SDK","modelcontextprotocol/registry":"Official & SDK",
 "modelcontextprotocol/modelcontextprotocol":"Official & SDK",
 "punkpeye/awesome-mcp-servers":"Registries & Awesome","yzfly/Awesome-MCP-ZH":"Registries & Awesome",
 "github/github-mcp-server":"Code & Dev tools","idosal/git-mcp":"Code & Dev tools",
 "DeusData/codebase-memory-mcp":"Code & Dev tools","wonderwhy-er/DesktopCommanderMCP":"Code & Dev tools",
 "microsoft/mcp-for-beginners":"Code & Dev tools","mark3labs/mcp-go":"Code & Dev tools","geelen/mcp-remote":"Code & Dev tools",
 "microsoft/playwright-mcp":"Browser & Web","ChromeDevTools/chrome-devtools-mcp":"Browser & Web",
 "hangwin/mcp-chrome":"Browser & Web","AgentDeskAI/browser-tools-mcp":"Browser & Web",
 "firecrawl/firecrawl-mcp-server":"Data & Scraping","apify/apify-mcp-server":"Data & Scraping","xpzouying/xiaohongshu-mcp":"Data & Scraping",
 "mongodb-js/mongodb-mcp-server":"Databases","googleapis/mcp-toolbox":"Databases","supabase/mcp":"Databases",
 "Cloudflare/mcp-server-cloudflare":"Cloud & Infrastructure","awslabs/mcp":"Cloud & Infrastructure",
 "firebase/firebase-tools":"Cloud & Infrastructure",
 "mrexodia/ida-pro-mcp":"Reverse Engineering","LaurieWired/GhidraMCP":"Reverse Engineering",
 "ahujasid/mcp-for-blender":"Design, 3D & Games","GLips/Figma-Context-MCP":"Design, 3D & Games",
 "CoplayDev/unity-mcp":"Design, 3D & Games","CursorTouch/Windows-MCP":"Design, 3D & Games","mobile-next/mobile-mcp":"Design, 3D & Games",
 "ComposioHQ/composio":"Agents & Frameworks","mcp-use/mcp-use":"Agents & Frameworks","lastmile-ai/mcp-agent":"Agents & Frameworks",
 "run-llama/llama_index":"Agents & Frameworks","tadata-org/fastapi_mcp":"Agents & Frameworks",
 "BeehiveInnovations/pal-mcp-server":"Agents & Frameworks","Ryze-AI-Adgent/open-seo-mcp-skills":"Agents & Frameworks",
 "n8n-io/n8n":"Workflow & Automation","czlonkowski/n8n-mcp":"Workflow & Automation",
}

def merge_record(fn, base):
    rec = dict(base)
    real = base.get("full_name") or fn  # prefer the API's real full_name (handles redirects/renames)
    rec["full_name"] = real
    rec["name"] = real.split("/")[-1]
    rec["owner"] = real.split("/")[0]
    return rec

servers = {}
# curated dict (may have only stars); key by the real full_name (API redirects)
for fn, d in meta["servers"].items():
    rec = merge_record(fn, d)
    key = rec["full_name"]
    rec["category"] = CAT.get(key, "Other")
    rec["scanned"] = key in SCANNED_FULL
    servers[key] = rec
# search_top (richer)
for it in meta.get("search_top", []):
    fn = it.get("full_name")
    if not fn:
        continue
    servers[fn] = merge_record(fn, it)
    servers[fn]["category"] = CAT.get(fn, "Other")
    servers[fn]["scanned"] = fn in SCANNED_FULL

slist = sorted(servers.values(), key=lambda r: (r.get("stars") or 0), reverse=True)

skills = {}
for fn, d in meta["skills"].items():
    rec = merge_record(fn, d)
    skills[rec["full_name"]] = rec
# add the fetched skills that landed in servers bucket (obra/superpowers etc.)
extra_skills = {}
for fn in ["obra/superpowers","davila7/claude-code-templates","hesreallyhim/awesome-claude-code","wshobson/agents"]:
    if fn in meta["servers"]:
        extra_skills[fn] = meta["servers"][fn]
        del servers[fn]
        slist = [r for r in slist if r["full_name"] != fn]
for fn, d in extra_skills.items():
    skills[fn] = merge_record(fn, d)
skills["anthropics/skills"]["category"] = "Official (Anthropic)"
skills["anthropics/claude-code"]["category"] = "Coding agent (with skills)"
skills["anthropics/claude-cookbooks"]["category"] = "Cookbook / recipes"
skills["obra/superpowers"]["category"] = "Skills framework"
skills["davila7/claude-code-templates"]["category"] = "Registry / templates"
skills["hesreallyhim/awesome-claude-code"]["category"] = "Awesome list"
skills["wshobson/agents"]["category"] = "Multi-agent skills"
sklist = sorted(skills.values(), key=lambda r: (r.get("stars") or 0), reverse=True)

def cats(lst):
    c = {}
    for r in lst:
        c[r.get("category","Other")] = c.get(r.get("category","Other"),0)+1
    return dict(sorted(c.items(), key=lambda x:-x[1]))

now = "2026-11-10"
data_dir = os.path.join(ROOT, "data")
os.makedirs(data_dir, exist_ok=True)
json.dump({"as_of": now, "count": len(slist), "servers": slist, "categories": cats(slist)},
          open(os.path.join(data_dir, "servers.json"), "w"), indent=2)
json.dump({"as_of": now, "count": len(sklist), "skills": sklist, "categories": cats(sklist)},
          open(os.path.join(data_dir, "skills.json"), "w"), indent=2)
json.dump({
    "as_of": now,
    "github_mcp_in_name_total": meta.get("search_total"),
    "note": "Count of public GitHub repositories with 'mcp' in the name (GitHub search, "
            "as_of date). A broad upper bound on the ecosystem, not a deduped server count.",
    "top_categories": cats(slist),
    "scanned_repos": sorted(SCANNED_FULL),
}, open(os.path.join(data_dir, "ecosystem.json"), "w"), indent=2)
print("servers:", len(slist), "skills:", len(sklist))
print("server categories:", cats(slist))
print("skill categories:", cats(sklist))
print("top 8 servers:", [f"{r['full_name']} ({r.get('stars')})" for r in slist[:8]])
print("top 5 skills:", [f"{r['full_name']} ({r.get('stars')})" for r in sklist[:5]])
print("scanned among servers:", [r['full_name'] for r in slist if r.get('scanned')])
