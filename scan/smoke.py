import importlib.util as u
s = u.spec_from_file_location("g", "gardu_scan.py"); m = u.module_from_spec(s); s.loader.exec_module(m)
for name in ("servers", "skills", "github-mcp-server", "DesktopCommanderMCP", "mcp-remote", "mcp-server-cloudflare", "mongodb-mcp-server"):
    r = m.scan_repo(name)
    if not r:
        print(name, "MISSING"); continue
    print(f"{r['repo']:<24} {r['verdict']:<7} real={r['findings_real']:<4} high={r['high']:<3} med={r['medium']:<4} rules={r['rules']}")
