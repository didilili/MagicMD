from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def scan_markdown_quality(markdown: str) -> list[str]:
    prose_markdown = _without_fenced_code(markdown)
    checks = {
        "empty_code_fence": _has_empty_code_fence(markdown),
        "image_used_as_heading": bool(re.search(r"^#{1,6}\s+(Image|!\[)", prose_markdown, re.MULTILINE)),
        "fragmented_recommendation_text": bool(
            re.search(r"推\*{2,}荐\*{2,}阅\*{2,}读", prose_markdown)
        ),
        "fragmented_bold_text": bool(re.search(r"\*\*[^*\n]{1,12}\*{4,}[^*\n]{1,12}\*\*", prose_markdown)),
        "broken_numbered_link_emphasis": bool(re.search(r"\*{3,}\d+[.．]\*{3,}\s*\[", prose_markdown)),
        "broken_linked_image": "[\n\n![Image]" in prose_markdown or "\n\n](" in prose_markdown,
    }
    return [name for name, matched in checks.items() if matched]


def build_package_quality(url: str, package_dir: str | Path) -> dict[str, Any]:
    package_path = Path(package_dir)
    metadata = _read_json(package_path / "metadata.json")
    article_path = package_path / "article.md"
    markdown = article_path.read_text(encoding="utf-8") if article_path.exists() else ""
    extraction = metadata.get("extraction") if isinstance(metadata.get("extraction"), dict) else {}
    images = metadata.get("images") if isinstance(metadata.get("images"), list) else []

    quality_issues = scan_markdown_quality(markdown)
    if not article_path.exists():
        quality_issues.append("missing_article_markdown")
    if not metadata:
        quality_issues.append("missing_metadata")
    warnings = list(extraction.get("warnings") or [])
    content_not_found = next((warning for warning in warnings if warning.endswith("_content_not_found")), "")

    return {
        "url": url,
        "status": "fail" if content_not_found else "ok",
        "title": str(metadata.get("title") or ""),
        "platform": str(metadata.get("platform") or ""),
        "source_url": str(metadata.get("source_url") or url),
        "package_dir": str(package_path),
        "warnings": warnings,
        "quality_issues": quality_issues,
        "image_count": len(images),
        "video_count": markdown.count("[视频](") + markdown.count("[Video]("),
        **({"error": content_not_found} if content_not_found else {}),
    }


def build_failure_quality(url: str, error: Exception) -> dict[str, Any]:
    return {
        "url": url,
        "status": "fail",
        "title": "",
        "platform": "",
        "fetcher": "",
        "stage": "convert",
        "elapsed_ms": 0,
        "max_attempts": 1,
        "retry_enabled": False,
        "source_url": url,
        "package_dir": "",
        "warnings": [],
        "quality_issues": [],
        "image_count": 0,
        "video_count": 0,
        "error": str(error),
    }


def write_batch_report(results: list[dict[str, Any]], output_dir: str | Path) -> dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": _summarize(results),
        "items": results,
    }
    json_path = output_path / "batch-report.json"
    markdown_path = output_path / "batch-report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown_report(payload), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _summarize(results: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(results),
        "ok": sum(1 for item in results if item.get("status") == "ok"),
        "failed": sum(1 for item in results if item.get("status") == "fail"),
        "with_warnings": sum(1 for item in results if item.get("warnings")),
        "with_quality_issues": sum(1 for item in results if item.get("quality_issues")),
    }


def _render_markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Batch Quality Report",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Total: {summary['total']}",
        f"- OK: {summary['ok']}",
        f"- Failed: {summary['failed']}",
        f"- With warnings: {summary['with_warnings']}",
        f"- With quality issues: {summary['with_quality_issues']}",
        "",
        "| Status | Platform | Fetcher | Stage | Time | Title | Warnings | Quality issues | Images | Videos | Attempts | Package / Error |",
        "| --- | --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in payload["items"]:
        package_or_error = item.get("package_dir") or item.get("error") or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    _table_cell(str(item.get("status") or "")),
                    _table_cell(str(item.get("platform") or "")),
                    _table_cell(str(item.get("fetcher") or "")),
                    _table_cell(str(item.get("stage") or "")),
                    _table_cell(_format_elapsed_ms(item.get("elapsed_ms"))),
                    _table_cell(str(item.get("title") or item.get("url") or "")),
                    _table_cell(", ".join(item.get("warnings") or [])),
                    _table_cell(", ".join(item.get("quality_issues") or [])),
                    str(item.get("image_count") or 0),
                    str(item.get("video_count") or 0),
                    str(item.get("max_attempts") or 1),
                    _table_cell(str(package_or_error)),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _has_empty_code_fence(markdown: str) -> bool:
    in_fence = False
    has_content = False
    for line in markdown.splitlines():
        if re.match(r"^`{3,}[a-zA-Z0-9_-]*\s*$", line):
            if in_fence:
                if not has_content:
                    return True
                in_fence = False
                has_content = False
            else:
                in_fence = True
                has_content = False
            continue
        if in_fence and line.strip():
            has_content = True
    return False


def _without_fenced_code(markdown: str) -> str:
    lines: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        if re.match(r"^`{3,}[a-zA-Z0-9_-]*\s*$", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _format_elapsed_ms(value: Any) -> str:
    if isinstance(value, int | float):
        return f"{int(value)} ms"
    return ""
