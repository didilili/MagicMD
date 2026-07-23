from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from magicmd.platforms.shared.markdown import (
    _FENCE_LINE_RE,
    _normalize_bare_urls,
    _normalize_strong_boundaries,
    _split_fenced_segments,
)

_EMPTY_IMAGE_TARGET_RE = re.compile(r"!\[[^\]\n]*\]\([ \t]*\)")
_RELATIVE_LOCAL_VIDEO_RE = re.compile(
    r"(?<!!)\[[^\]\n]*\]\([ \t]*<?(?:\./)?videos/[^)\s>]+>?",
    re.IGNORECASE,
)
_ESCAPED_STRONG_MARKER_RE = re.compile(r"\\\*\\\*(?:[^\\*\n](?:.*?[^\\*\n])?)\\\*\\\*")
_SHELL_FENCE_LANGUAGES = {
    "",
    "bash",
    "bat",
    "batch",
    "cmd",
    "console",
    "fish",
    "powershell",
    "pwsh",
    "sh",
    "shell",
    "terminal",
    "zsh",
}
_SHELL_COMMAND_RE = re.compile(
    r"^[ \t]*(?:(?:\$|>)[ \t]+)?(?:"
    r"(?:npm|pnpm|yarn|bun)[ \t]+"
    r"(?:add|ci|create|exec|install|remove|run|uninstall|update)(?:[ \t]|$)|"
    r"npx[ \t]+\S|pip3?[ \t]+install(?:[ \t]|$)|"
    r"python3?[ \t]+-m[ \t]+pip(?:[ \t]|$)|"
    r"git[ \t]+(?:clone|fetch|pull|push|submodule)(?:[ \t]|$)|"
    r"(?:curl|wget)[ \t]+\S|brew[ \t]+install(?:[ \t]|$)|"
    r"apt(?:-get)?[ \t]+install(?:[ \t]|$)|sudo[ \t]+\S|"
    r"docker[ \t]+(?:build|compose|pull|run)(?:[ \t]|$)|"
    r"kubectl[ \t]+(?:apply|create|get|run)(?:[ \t]|$)|"
    r"cargo[ \t]+install(?:[ \t]|$)"
    r")",
    re.MULTILINE,
)
_ADDRESS_ONLY_CODE_RE = re.compile(
    r"^[ \t]*(?:开源地址|项目地址|官网)[ \t]*[：:][ \t]*"
    r"https?://[^\s<>\n]+?[，。！？；：、]?[ \t]*$"
)
_HEADING_RE = re.compile(r"(?m)^[ \t]{0,3}(#{1,6})(?:[ \t]+|$)")
_EXTERNAL_WECHAT_MEDIA_RE = re.compile(
    r"!\[[^\]\n]*\]\([ \t]*<?https?://"
    r"(?:mmbiz\.qpic\.cn|mmbiz\.qlogo\.cn|mpvideo\.qpic\.cn)(?=[/:])"
    r"|(?<!!)\[(?:视频|Video)\]\([ \t]*<?https?://mpvideo\.qpic\.cn(?=[/:])",
    re.IGNORECASE,
)


def scan_markdown_quality(markdown: str) -> list[str]:
    fenced_segments = _split_fenced_segments(markdown)
    code_fences = _parse_code_fences(fenced_segments)
    prose_markdown = _without_inline_code(_without_fenced_code(markdown, segments=fenced_segments))
    checks = {
        "empty_code_fence": _has_empty_code_fence(code_fences),
        "image_used_as_heading": bool(
            re.search(r"^#{1,6}\s+(Image|!\[)", prose_markdown, re.MULTILINE)
        ),
        "fragmented_recommendation_text": bool(
            re.search(r"推\*{2,}荐\*{2,}阅\*{2,}读", prose_markdown)
        ),
        "fragmented_bold_text": bool(
            re.search(r"\*\*[^*\n]{1,12}\*{4,}[^*\n]{1,12}\*\*", prose_markdown)
        ),
        "broken_numbered_link_emphasis": bool(
            re.search(r"\*{3,}\d+[.．]\*{3,}\s*\[", prose_markdown)
        ),
        "broken_strong_boundary": _normalize_strong_boundaries(prose_markdown) != prose_markdown,
        "orphan_emphasis_marker": bool(re.search(r"(?m)^[ \t]*\*\*[ \t]*$", prose_markdown)),
        "redundant_emphasis_marker": bool(re.search(r"\*{4,}", prose_markdown)),
        "unbalanced_emphasis_marker": _has_unbalanced_emphasis_marker(prose_markdown),
        "broken_bare_url_boundary": _normalize_bare_urls(prose_markdown) != prose_markdown,
        "broken_linked_image": "[\n\n![Image]" in prose_markdown or "\n\n](" in prose_markdown,
        "empty_image_target": bool(_EMPTY_IMAGE_TARGET_RE.search(prose_markdown)),
        "relative_local_video": bool(_RELATIVE_LOCAL_VIDEO_RE.search(prose_markdown)),
        "escaped_strong_marker": bool(_ESCAPED_STRONG_MARKER_RE.search(prose_markdown)),
        "code_contains_nbsp": any("\u00a0" in content for _, content in code_fences),
        "suspicious_code_language": _has_suspicious_code_language(code_fences),
        "address_only_code_fence": any(
            _ADDRESS_ONLY_CODE_RE.fullmatch(content) for _, content in code_fences
        ),
        "heading_level_jump": _has_heading_level_jump(prose_markdown),
        "external_media_not_rewritten": bool(_EXTERNAL_WECHAT_MEDIA_RE.search(prose_markdown)),
    }
    return [name for name, matched in checks.items() if matched]


def build_package_quality(
    url: str,
    package_dir: str | Path,
    markdown_filename: str = "article.md",
    metadata_filename: str = "metadata.json",
) -> dict[str, Any]:
    package_path = Path(package_dir)
    metadata = _read_json(package_path / metadata_filename)
    article_path = package_path / markdown_filename
    markdown = article_path.read_text(encoding="utf-8") if article_path.exists() else ""
    extraction = metadata.get("extraction") if isinstance(metadata.get("extraction"), dict) else {}
    images = metadata.get("images") if isinstance(metadata.get("images"), list) else []

    quality_issues = scan_markdown_quality(markdown)
    if not article_path.exists():
        quality_issues.append("missing_article_markdown")
    if not metadata:
        quality_issues.append("missing_metadata")
    warnings = list(extraction.get("warnings") or [])
    content_not_found = next(
        (warning for warning in warnings if warning.endswith("_content_not_found")), ""
    )

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


def build_skipped_quality(
    url: str,
    package_dir: str | Path,
    markdown_filename: str = "article.md",
    metadata_filename: str = "metadata.json",
) -> dict[str, Any]:
    item = build_package_quality(
        url,
        package_dir,
        markdown_filename=markdown_filename,
        metadata_filename=metadata_filename,
    )
    item["status"] = "skipped"
    item.pop("error", None)
    return item


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
        "skipped": sum(1 for item in results if item.get("status") == "skipped"),
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
        f"- Skipped: {summary['skipped']}",
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


def _has_empty_code_fence(code_fences: list[tuple[str, str]]) -> bool:
    return any(not content.strip() for _, content in code_fences)


def _without_fenced_code(
    markdown: str,
    *,
    segments: list[tuple[bool, str]] | None = None,
) -> str:
    parsed_segments = segments if segments is not None else _split_fenced_segments(markdown)
    return "".join(segment for is_code, segment in parsed_segments if not is_code)


def _parse_code_fences(
    segments: list[tuple[bool, str]],
) -> list[tuple[str, str]]:
    code_fences: list[tuple[str, str]] = []
    for is_code, segment in segments:
        if not is_code:
            continue
        lines = segment.splitlines()
        if not lines:
            continue
        opening = _FENCE_LINE_RE.match(lines[0])
        if not opening:
            continue
        opening_fence = opening.group("fence")
        info_string = opening.group("tail").strip()
        language = info_string.split(maxsplit=1)[0].lower() if info_string else ""
        language = language.removeprefix("{.").removesuffix("}")

        content_lines = lines[1:]
        if content_lines:
            closing = _FENCE_LINE_RE.match(content_lines[-1])
            if (
                closing
                and closing.group("fence")[0] == opening_fence[0]
                and len(closing.group("fence")) >= len(opening_fence)
                and not closing.group("tail").strip()
            ):
                content_lines.pop()
        code_fences.append((language, "\n".join(content_lines)))
    return code_fences


def _has_suspicious_code_language(code_fences: list[tuple[str, str]]) -> bool:
    return any(
        language not in _SHELL_FENCE_LANGUAGES and _SHELL_COMMAND_RE.search(content)
        for language, content in code_fences
    )


def _has_heading_level_jump(markdown: str) -> bool:
    previous_level: int | None = None
    for match in _HEADING_RE.finditer(markdown):
        level = len(match.group(1))
        if previous_level is not None and level > previous_level + 1:
            return True
        previous_level = level
    return False


def _without_inline_code(markdown: str) -> str:
    return re.sub(r"(`+)([^\n]*?)\1", "", markdown)


def _has_unbalanced_emphasis_marker(markdown: str) -> bool:
    stray_bold_inside_italic = re.compile(r"(?<!\*)\*(?!\*)[^*\n]*\*\*(?!\*)[^*\n]*\*(?!\*)")
    valid_nested_bold_italic = re.compile(r"\*\*[^*\n]*\*[^*\n]+\*{3}")
    exact_strong_marker = re.compile(r"(?<!\*)\*\*(?!\*)")

    for line in markdown.splitlines():
        if stray_bold_inside_italic.search(line):
            return True
        if len(exact_strong_marker.findall(line)) % 2 == 0:
            continue
        if valid_nested_bold_italic.fullmatch(line.strip()):
            continue
        return True
    return False


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


def repair_markdown_quality(markdown: str) -> str:
    from magicmd.platforms.shared.markdown import (
        repair_markdown_quality as repair,
    )

    return repair(markdown)
