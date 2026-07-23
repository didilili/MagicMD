from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from magicmd.platforms.shared.markdown import (
    _FENCE_LINE_RE,
    _normalize_bare_urls,
    _normalize_strong_boundaries,
    _split_fenced_segments,
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
    "sh-session",
    "shell",
    "shell-session",
    "terminal",
    "zsh",
}
_COMMAND_CONTAINER_LANGUAGES = {"make", "makefile", "yaml", "yml"}
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
_VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm"}
_WECHAT_IMAGE_HOSTS = {"mmbiz.qlogo.cn", "mmbiz.qpic.cn", "mpvideo.qpic.cn"}
_BLOCKQUOTE_PREFIX_RE = re.compile(r"[ \t]{0,3}>[ \t]?")
_LIST_CONTAINER_RE = re.compile(r"[ \t]{0,3}(?:[-+*]|\d+[.)])[ \t]+$")
_REFERENCE_DEFINITION_RE = re.compile(
    r"(?m)^[ \t]{0,3}\[(?P<label>[^\]\r\n]+)\]:[ \t]*(?P<payload>[^\r\n]*)$"
)
_AUTOLINK_RE = re.compile(
    r"<(?P<destination>(?:https?://|mailto:)[^<>\s]*)>",
    re.IGNORECASE,
)
_RELATIVE_PATH_PREFIX_RE = re.compile(r"^(?:(?:\.\.?/)|/)+")


@dataclass(frozen=True)
class _MarkdownDestination:
    is_image: bool
    destination: str
    payload_start: int
    payload_end: int


@dataclass(frozen=True)
class _ReferenceDefinition:
    destination: str


def scan_markdown_quality(markdown: str) -> list[str]:
    fenced_segments = _split_fenced_segments(markdown)
    code_fences = _parse_code_fences(fenced_segments)
    prose_markdown = _without_inline_code(_without_fenced_code(markdown, segments=fenced_segments))
    reference_definitions, reference_definition_spans = _parse_reference_definitions(prose_markdown)
    destinations = list(_iter_markdown_destinations(prose_markdown, reference_definitions))
    masked_destination_markdown = _mask_markdown_destination_payloads(
        prose_markdown,
        destinations,
        extra_spans=reference_definition_spans
        + [
            (match.start("destination"), match.end("destination"))
            for match in _AUTOLINK_RE.finditer(prose_markdown)
        ],
    )
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
        "broken_strong_boundary": (
            _normalize_strong_boundaries(masked_destination_markdown) != masked_destination_markdown
        ),
        "orphan_emphasis_marker": bool(
            re.search(r"(?m)^[ \t]*\*\*[ \t]*$", masked_destination_markdown)
        ),
        "redundant_emphasis_marker": bool(re.search(r"\*{4,}", masked_destination_markdown)),
        "unbalanced_emphasis_marker": _has_unbalanced_emphasis_marker(masked_destination_markdown),
        "broken_bare_url_boundary": (
            _normalize_bare_urls(masked_destination_markdown) != masked_destination_markdown
        ),
        "broken_linked_image": "[\n\n![Image]" in prose_markdown or "\n\n](" in prose_markdown,
        "empty_image_target": any(item.is_image and not item.destination for item in destinations),
        "relative_local_video": any(
            _is_relative_local_video(item.destination) for item in destinations
        ),
        "escaped_strong_marker": bool(
            _ESCAPED_STRONG_MARKER_RE.search(masked_destination_markdown)
        ),
        "code_contains_nbsp": any("\u00a0" in content for _, content in code_fences),
        "suspicious_code_language": _has_suspicious_code_language(code_fences),
        "address_only_code_fence": any(
            _ADDRESS_ONLY_CODE_RE.fullmatch(content) for _, content in code_fences
        ),
        "heading_level_jump": _has_heading_level_jump(prose_markdown),
        "external_media_not_rewritten": any(
            _is_external_wechat_media(item) for item in destinations
        ),
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
        container = opening.group("container")
        blockquote_depth = container.count(">")
        after_blockquotes = container.rsplit(">", maxsplit=1)[-1]
        if blockquote_depth:
            after_blockquotes = after_blockquotes.lstrip(" \t")
        list_match = _LIST_CONTAINER_RE.search(after_blockquotes)
        list_indent = len(list_match.group(0)) if list_match else 0

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
        content_lines = [
            _strip_fence_container_prefix(line, blockquote_depth, list_indent)
            for line in content_lines
        ]
        code_fences.append((language, "\n".join(content_lines)))
    return code_fences


def _strip_fence_container_prefix(
    line: str,
    blockquote_depth: int,
    list_indent: int,
) -> str:
    position = 0
    for _ in range(blockquote_depth):
        match = _BLOCKQUOTE_PREFIX_RE.match(line, position)
        if not match:
            return line
        position = match.end()

    if not list_indent:
        return line[position:]

    indentation_end = position
    while indentation_end < len(line) and line[indentation_end] in " \t":
        indentation_end += 1
    if indentation_end - position < list_indent:
        return line[position:]
    return line[position + list_indent :]


def _has_suspicious_code_language(code_fences: list[tuple[str, str]]) -> bool:
    return any(
        language not in _SHELL_FENCE_LANGUAGES
        and language not in _COMMAND_CONTAINER_LANGUAGES
        and _SHELL_COMMAND_RE.search(content)
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
    return re.sub(r"(`+)([^\n]*?)\1", " ", markdown)


def _has_unbalanced_emphasis_marker(markdown: str) -> bool:
    return any(
        _has_unbalanced_emphasis_block(block) for block in re.split(r"\r?\n[ \t]*\r?\n", markdown)
    )


def _has_unbalanced_emphasis_block(markdown: str) -> bool:
    open_strong_markers = 0
    position = 0
    while position < len(markdown):
        if markdown[position] != "*":
            position += 1
            continue
        run_end = position + 1
        while run_end < len(markdown) and markdown[run_end] == "*":
            run_end += 1
        if _is_escaped_character(markdown, position):
            position = run_end
            continue

        strong_marker_count = (run_end - position) // 2
        if not strong_marker_count:
            position = run_end
            continue
        before = markdown[position - 1] if position else ""
        after = markdown[run_end] if run_end < len(markdown) else ""
        before_is_whitespace = not before or before.isspace()
        after_is_whitespace = not after or after.isspace()
        before_is_punctuation = _is_punctuation(before)
        after_is_punctuation = _is_punctuation(after)
        can_open = not after_is_whitespace and (
            not after_is_punctuation or before_is_whitespace or before_is_punctuation
        )
        can_close = not before_is_whitespace and (
            not before_is_punctuation or after_is_whitespace or after_is_punctuation
        )

        for _ in range(strong_marker_count):
            if can_close and open_strong_markers:
                open_strong_markers -= 1
            elif can_open:
                open_strong_markers += 1
            elif can_close:
                return True
        position = run_end
    return bool(open_strong_markers)


def _is_escaped_character(value: str, position: int) -> bool:
    backslash_count = 0
    position -= 1
    while position >= 0 and value[position] == "\\":
        backslash_count += 1
        position -= 1
    return backslash_count % 2 == 1


def _is_punctuation(value: str) -> bool:
    return bool(value) and unicodedata.category(value).startswith("P")


def _iter_markdown_destinations(
    markdown: str,
    reference_definitions: dict[str, _ReferenceDefinition],
) -> Iterator[_MarkdownDestination]:
    label_ends = _build_markdown_label_ends(markdown)
    ranges = [(0, len(markdown))]

    while ranges:
        position, range_end = ranges.pop()
        while position < range_end:
            if markdown.startswith("![", position):
                is_image = True
                label_start = position + 1
            elif markdown[position] == "[" and (position == 0 or markdown[position - 1] != "!"):
                is_image = False
                label_start = position
            else:
                position += 1
                continue

            label_end = label_ends.get(label_start)
            if label_end is None or label_end >= range_end:
                position = label_start + 1
                continue
            if _is_reference_definition_label(markdown, label_start, label_end):
                position = label_end + 1
                continue

            destination: str | None = None
            payload_start = 0
            payload_end = 0
            continuation_start = label_end + 1
            if continuation_start < range_end and markdown[continuation_start] == "(":
                payload_start = continuation_start + 1
                payload = _parse_markdown_destination_payload(markdown, payload_start)
                if payload is None:
                    next_line = markdown.find("\n", payload_start, range_end)
                    continuation_start = range_end if next_line < 0 else next_line + 1
                    ranges.append((continuation_start, range_end))
                    ranges.append((label_start + 1, label_end))
                    break
                destination, payload_end = payload
                continuation_start = payload_end + 1
            else:
                reference = _resolve_reference_destination(
                    markdown,
                    label_start,
                    label_end,
                    range_end,
                    label_ends,
                    reference_definitions,
                )
                if reference is None:
                    position = label_start + 1
                    continue
                definition, continuation_start = reference
                destination = definition.destination

            yield _MarkdownDestination(
                is_image=is_image,
                destination=destination,
                payload_start=payload_start,
                payload_end=payload_end,
            )
            ranges.append((continuation_start, range_end))
            ranges.append((label_start + 1, label_end))
            break


def _resolve_reference_destination(
    markdown: str,
    label_start: int,
    label_end: int,
    range_end: int,
    label_ends: dict[int, int],
    reference_definitions: dict[str, _ReferenceDefinition],
) -> tuple[_ReferenceDefinition, int] | None:
    visible_label = markdown[label_start + 1 : label_end]
    continuation_start = label_end + 1
    reference_label = visible_label
    if continuation_start < range_end and markdown[continuation_start] == "[":
        reference_end = label_ends.get(continuation_start)
        if reference_end is None or reference_end >= range_end:
            return None
        explicit_label = markdown[continuation_start + 1 : reference_end]
        reference_label = explicit_label or visible_label
        continuation_start = reference_end + 1
    normalized_label = _normalize_reference_label(reference_label)
    definition = reference_definitions.get(normalized_label)
    if definition is None:
        return None
    return definition, continuation_start


def _is_reference_definition_label(
    markdown: str,
    label_start: int,
    label_end: int,
) -> bool:
    if label_end + 1 >= len(markdown) or markdown[label_end + 1] != ":":
        return False
    line_start = markdown.rfind("\n", 0, label_start) + 1
    indentation = markdown[line_start:label_start]
    return len(indentation) <= 3 and not indentation.strip(" \t")


def _parse_reference_definitions(
    markdown: str,
) -> tuple[dict[str, _ReferenceDefinition], list[tuple[int, int]]]:
    definitions: dict[str, _ReferenceDefinition] = {}
    payload_spans: list[tuple[int, int]] = []
    for match in _REFERENCE_DEFINITION_RE.finditer(markdown):
        normalized_label = _normalize_reference_label(match.group("label"))
        if not normalized_label:
            continue
        parsed = _parse_reference_definition_payload(
            markdown,
            match.start("payload"),
            match.end("payload"),
        )
        if parsed is None:
            continue
        destination, destination_start = parsed
        payload_end = match.end("payload")
        payload_spans.append((destination_start, payload_end))
        definitions.setdefault(
            normalized_label,
            _ReferenceDefinition(
                destination=destination,
            ),
        )
    return definitions, payload_spans


def _parse_reference_definition_payload(
    markdown: str,
    payload_start: int,
    payload_end: int,
) -> tuple[str, int] | None:
    position = payload_start
    while position < payload_end and markdown[position] in " \t":
        position += 1
    if position >= payload_end:
        return None
    if markdown[position] == "<":
        destination_start = position + 1
        closing = markdown.find(">", destination_start, payload_end)
        if closing < 0:
            return None
        return markdown[destination_start:closing], position

    destination_start = position
    parenthesis_depth = 0
    while position < payload_end:
        character = markdown[position]
        if character == "\\":
            position += 2
            continue
        if character == "(":
            parenthesis_depth += 1
        elif character == ")" and parenthesis_depth:
            parenthesis_depth -= 1
        elif character in " \t" and not parenthesis_depth:
            break
        position += 1
    return markdown[destination_start:position], destination_start


def _normalize_reference_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip()).casefold()


def _build_markdown_label_ends(markdown: str) -> dict[int, int]:
    opening_brackets: list[int] = []
    label_ends: dict[int, int] = {}
    position = 0
    while position < len(markdown):
        if markdown[position] == "\\":
            position += 2
            continue
        if markdown[position] == "[":
            opening_brackets.append(position)
        elif markdown[position] == "]" and opening_brackets:
            label_ends[opening_brackets.pop()] = position
        position += 1
    return label_ends


def _parse_markdown_destination_payload(
    markdown: str,
    payload_start: int,
) -> tuple[str, int] | None:
    if payload_start >= len(markdown):
        return None
    if markdown[payload_start] == ")":
        return "", payload_start
    position = _skip_markdown_whitespace(markdown, payload_start)
    if position >= len(markdown):
        return None
    if markdown[position] == ")":
        return None

    if markdown[position] == "<":
        destination_start = position + 1
        position = destination_start
        while position < len(markdown):
            if markdown[position] in "\r\n":
                return None
            if markdown[position] == "\\":
                position += 2
                continue
            if markdown[position] == ">":
                destination = markdown[destination_start:position]
                return _finish_markdown_destination(markdown, destination, position + 1)
            position += 1
        return None

    destination_start = position
    parenthesis_depth = 0
    while position < len(markdown):
        character = markdown[position]
        if character == "\\":
            position += 2
            continue
        if character == "(":
            parenthesis_depth += 1
        elif character == ")":
            if not parenthesis_depth:
                return markdown[destination_start:position], position
            parenthesis_depth -= 1
        elif character.isspace() and not parenthesis_depth:
            destination = markdown[destination_start:position]
            return _finish_markdown_destination(markdown, destination, position)
        position += 1
    return None


def _finish_markdown_destination(
    markdown: str,
    destination: str,
    position: int | None,
) -> tuple[str, int] | None:
    if position is None:
        return None
    whitespace_end = _skip_markdown_whitespace(markdown, position)
    if whitespace_end >= len(markdown):
        return None
    if markdown[whitespace_end] == ")":
        return destination, whitespace_end
    if whitespace_end == position or markdown[whitespace_end] not in "\"'(":
        return None
    title_end = _parse_markdown_title(markdown, whitespace_end)
    if title_end is None:
        return None
    closing_position = _skip_markdown_whitespace(markdown, title_end)
    if closing_position >= len(markdown) or markdown[closing_position] != ")":
        return None
    return destination, closing_position


def _parse_markdown_title(markdown: str, position: int) -> int | None:
    opener = markdown[position]
    closer = ")" if opener == "(" else opener
    depth = 1
    position += 1
    while position < len(markdown):
        if markdown[position] == "\\":
            position += 2
            continue
        if opener == "(" and markdown[position] == "(":
            depth += 1
        elif markdown[position] == closer:
            depth -= 1
            if not depth:
                return position + 1
        position += 1
    return None


def _skip_markdown_whitespace(markdown: str, position: int) -> int:
    while position < len(markdown) and markdown[position].isspace():
        position += 1
    return position


def _mask_markdown_destination_payloads(
    markdown: str,
    destinations: list[_MarkdownDestination],
    *,
    extra_spans: list[tuple[int, int]] | None = None,
) -> str:
    characters = list(markdown)
    spans = [
        (item.payload_start, item.payload_end)
        for item in destinations
        if item.payload_end > item.payload_start
    ]
    spans.extend(extra_spans or [])
    for start, end in spans:
        for position in range(start, end):
            if characters[position] not in "\r\n":
                characters[position] = " "
    return "".join(characters)


def _is_relative_local_video(destination: str) -> bool:
    if not destination or destination.startswith("//"):
        return False
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc:
        return False
    path = re.split(r"[?#]", destination, maxsplit=1)[0].lower()
    prefix = _RELATIVE_PATH_PREFIX_RE.match(path)
    if prefix:
        path = path[prefix.end() :]
    if not path.startswith("videos/"):
        return False
    return any(path.endswith(extension) for extension in _VIDEO_EXTENSIONS)


def _is_external_wechat_media(item: _MarkdownDestination) -> bool:
    destination = item.destination
    if destination.startswith("//"):
        destination = f"https:{destination}"
    parsed = urlsplit(destination)
    hostname = (parsed.hostname or "").lower()
    return hostname == "mpvideo.qpic.cn" or (item.is_image and hostname in _WECHAT_IMAGE_HOSTS)


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
