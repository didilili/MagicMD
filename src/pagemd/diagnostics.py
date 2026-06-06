from __future__ import annotations

import json
from pathlib import Path


def save_debug_html(output_dir: str | Path, html: str) -> Path:
    path = Path(output_dir) / "debug.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def save_extraction_report(output_dir: str | Path, report: dict) -> Path:
    path = Path(output_dir) / "extraction-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path

