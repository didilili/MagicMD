from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from magicmd import __version__
from magicmd.config import MagicMDConfig, load_config


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


def build_doctor_report(
    config_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    config, config_status = _load_doctor_config(config_path)
    resolved_output = Path(output_dir or config.output.directory)
    output_status = _check_output_writable(resolved_output)
    camoufox_available = importlib.util.find_spec("camoufox") is not None

    return {
        "python": ".".join(str(part) for part in sys.version_info[:3]),
        "magicmd": _package_version(),
        "config": config_status,
        "output": output_status,
        "camoufox": "available" if camoufox_available else "missing",
        "platforms": [
            {
                "name": name,
                "browser": platform.browser,
                "wait_selector": platform.wait_selector,
                "enabled": platform.enabled,
            }
            for name, platform in config.platforms.items()
        ],
        "ok": config_status["ok"] and output_status["ok"] and camoufox_available,
    }


def render_doctor_report(report: dict[str, Any]) -> str:
    lines = [
        "MagicMD doctor",
        "",
        f"{_mark(True)} Python: {report['python']}",
        f"{_mark(True)} MagicMD: {report['magicmd']}",
        f"{_mark(report['config']['ok'])} Config: {report['config']['message']}",
        f"{_mark(report['output']['ok'])} Output: {report['output']['message']}",
        f"{_mark(report['camoufox'] == 'available')} Camoufox: {report['camoufox']}",
        f"{_mark(True)} Platforms:",
    ]
    for platform in report["platforms"]:
        selector = f", {platform['wait_selector']}" if platform["wait_selector"] else ""
        enabled = "" if platform["enabled"] else " (disabled)"
        lines.append(f"  - {platform['name']}: {platform['browser']}{selector}{enabled}")
    return "\n".join(lines) + "\n"


def _load_doctor_config(config_path: str | Path | None) -> tuple[MagicMDConfig, dict[str, Any]]:
    if config_path:
        path = Path(config_path)
        try:
            return load_config(path), {"ok": True, "message": f"{path} loaded"}
        except Exception as exc:
            return MagicMDConfig(), {"ok": False, "message": f"{path} invalid: {exc}"}

    default_path = Path(".magicmd.toml")
    if default_path.exists():
        try:
            return load_config(default_path), {"ok": True, "message": f"{default_path} loaded"}
        except Exception as exc:
            return MagicMDConfig(), {"ok": False, "message": f"{default_path} invalid: {exc}"}
    return load_config(), {"ok": True, "message": ".magicmd.toml not found, using defaults"}


def _check_output_writable(output_dir: Path) -> dict[str, Any]:
    target = output_dir if output_dir.exists() else _nearest_existing_parent(output_dir)
    try:
        with tempfile.NamedTemporaryFile(prefix=".magicmd-doctor-", dir=target, delete=True):
            pass
        state = "writable" if output_dir.exists() else "creatable"
        return {"ok": True, "message": f"{output_dir} {state}"}
    except Exception as exc:
        return {"ok": False, "message": f"{output_dir} not writable: {exc}"}


def _nearest_existing_parent(path: Path) -> Path:
    current = path.parent
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def _package_version() -> str:
    try:
        return importlib.metadata.version("magicmd")
    except importlib.metadata.PackageNotFoundError:
        return __version__


def _mark(ok: bool) -> str:
    return "✓" if ok else "✗"
