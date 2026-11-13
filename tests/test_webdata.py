"""The published web/data.js must be readable JSON that matches the source datasets."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = "window.MCPDATA = "


def load_web_payload():
    text = (ROOT / "web" / "data.js").read_text(encoding="utf-8")
    body = text[text.index(HEADER) + len(HEADER):].rstrip().rstrip(";")
    return text, json.loads(body)


class WebData(unittest.TestCase):
    def test_data_js_is_plain_readable_json(self):
        text, payload = load_web_payload()
        self.assertGreater(text.count("\n"), 100, "data.js should be indented, not one long line")
        self.assertEqual(payload["meta"]["brand"], "Gardu")

    def test_rows_match_the_source_datasets(self):
        _, payload = load_web_payload()
        servers = json.loads((ROOT / "data" / "servers.json").read_text(encoding="utf-8"))
        skills = json.loads((ROOT / "data" / "skills.json").read_text(encoding="utf-8"))
        scan = json.loads((ROOT / "data" / "scan.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["servers"]["servers"]), len(servers["servers"]))
        self.assertEqual(len(payload["skills"]["skills"]), len(skills["skills"]))
        self.assertEqual(payload["scan"]["totals"], scan["totals"])
        self.assertEqual(len(payload["scan"]["results"]), len(scan["results"]))


if __name__ == "__main__":
    unittest.main()
