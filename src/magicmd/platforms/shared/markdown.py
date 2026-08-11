from __future__ import annotations

from collections.abc import Callable
import re
import unicodedata

import markdownify
from bs4 import BeautifulSoup, NavigableString, Tag


_FENCED_CODE_BLOCK_RE = re.compile(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$")
_INLINE_CODE_RE = re.compile(r"(`+)([^\n]*?)\1")
_FENCE_LINE_RE = re.compile(
    r"^(?P<container>"
    r"(?:(?:[ \t]{0,3}>[ \t]?)+)?"
    r"(?:[ \t]{0,3}(?:[-+*]|\d+[.)])[ \t]+)?"
    r"[ \t]{0,3}"
    r")"
    r"(?P<fence>`{3,}|~{3,})(?P<tail>.*)$"
)
_ADDRESS_ONLY_FENCE_RE = re.compile(
    r"^(?P<fence>`{3,}|~{3,})[^\n]*\r?\n"
    r"(?P<label>[ \t]*(?:开源地址|项目地址|官网)[ \t]*[：:][ \t]*)"
    r"(?P<url>https?://[^\s<>\n]+?)(?P<terminal>[，。！？；：、]?)[ \t]*\r?\n"
    r"(?P=fence)[ \t]*(?P<ending>\r?\n)?$"
)
_PAIRED_ESCAPED_STRONG_RE = re.compile(r"\\\*\\\*(?P<text>[^\\*\n](?:.*?[^\\*\n])?)\\\*\\\*")
_BARE_URL_RE = re.compile(
    r"(?<![<(])(?P<url>https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+)"
    r"(?=[，。！？；：、\u4e00-\u9fff])"
)
_MARKDOWN_IMAGE_PATTERN = r"!\[[^\]\n]*\]\((?:[^()\n]|\([^()\n]*\))*\)"
_ORPHAN_IMAGE_EMPHASIS_RE = re.compile(
    r"(?m)^[ \t]*\*\*[ \t]*\r?\n"
    r"(?:[ \t]*\r?\n)*"
    rf"(?P<image>{_MARKDOWN_IMAGE_PATTERN})[ \t]*\r?\n"
    r"(?:[ \t]*\r?\n)*"
    r"[ \t]*\*\*[ \t]*$"
)
_ORPHAN_IMAGE_PREFIX_RE = re.compile(
    r"(?m)^[ \t]*\*\*[ \t]*\r?\n"
    r"(?:[ \t]*\r?\n)*"
    rf"(?P<image>{_MARKDOWN_IMAGE_PATTERN})[ \t]*$"
)
_STRONG_BOUNDARY_PUNCTUATION = r":："
_STRONG_PRECEDING_TEXT = r"\w\u4e00-\u9fff"
_STRONG_OPEN = rf"(?<![{_STRONG_PRECEDING_TEXT}])\*\*(?![ \t*])"
_STRONG_SPAN_RE = re.compile(r"(?<!\*)\*\*(?!\*)(?P<text>[^*\n]+?)(?<!\*)\*\*(?!\*)")
_PAIRED_PUNCTUATION = {
    "(": ")",
    "[": "]",
    "{": "}",
    "“": "”",
    "‘": "’",
    "（": "）",
    "【": "】",
    "《": "》",
    "〈": "〉",
    "「": "」",
    "『": "』",
}
_TRAILING_GROUP_PAIRS = (("（", "）"), ("(", ")"))
_UNORDERED_LIST_BULLET_RE = re.compile(r"^\s*[•●○◦▪▫][ \t]*")
_ORDERED_LIST_NUMBER_RE = re.compile(r"^\s*(?P<number>\d+)[.．、][ \t]*")
_LIST_MARKER_PROTECTED_ELEMENTS = {"code", "pre", "ul", "ol"}


def _is_punctuation(value: str) -> bool:
    return bool(value) and unicodedata.category(value).startswith("P")


def _is_text_character(value: str) -> bool:
    if not value:
        return False
    category = unicodedata.category(value)
    return value == "_" or category.startswith(("L", "N"))


def _strip_image_emphasis(md: str) -> str:
    pattern = re.compile(rf"(?<!\*)\*{{1,3}}(?P<image>{_MARKDOWN_IMAGE_PATTERN})\*{{1,3}}(?!\*)")

    def strip_wrapper(match: re.Match[str]) -> str:
        line_start = md.rfind("\n", 0, match.start()) + 1
        if _has_unclosed_strong_marker(md[line_start : match.start()]):
            return match.group(0)
        return match.group("image")

    return pattern.sub(strip_wrapper, md)


def _has_unclosed_strong_marker(value: str) -> bool:
    marker_count = 0
    position = 0
    while position < len(value):
        if value[position] != "*":
            position += 1
            continue
        run_end = position + 1
        while run_end < len(value) and value[run_end] == "*":
            run_end += 1
        backslashes = 0
        escape_position = position - 1
        while escape_position >= 0 and value[escape_position] == "\\":
            backslashes += 1
            escape_position -= 1
        if backslashes % 2 == 0:
            marker_count += (run_end - position) // 2
        position = run_end
    return marker_count % 2 == 1


def _normalize_bare_urls(md: str) -> str:
    def normalize_prose(segment: str) -> str:
        return _BARE_URL_RE.sub(r"<\g<url>>", segment)

    parts: list[str] = []
    cursor = 0
    for match in _INLINE_CODE_RE.finditer(md):
        parts.append(normalize_prose(md[cursor : match.start()]))
        parts.append(match.group(0))
        cursor = match.end()
    parts.append(normalize_prose(md[cursor:]))
    return "".join(parts)


def _separate_markdown_images(md: str) -> str:
    md, empty_image_count = re.subn(r"!\[[^\]]*\]\(\s*\)", "", md)
    md = re.sub(rf"([^\[\n])({_MARKDOWN_IMAGE_PATTERN})", r"\1\n\n\2", md)
    md = re.sub(rf"({_MARKDOWN_IMAGE_PATTERN})([^\]\n])", r"\1\n\n\2", md)
    md = re.sub(
        rf"({_MARKDOWN_IMAGE_PATTERN})\s*({_MARKDOWN_IMAGE_PATTERN})",
        r"\1\n\n\2",
        md,
    )
    if empty_image_count:
        md = re.sub(r"\n{3,}", "\n\n", md)
    return md


def _promote_numbered_markdown_headings(md: str) -> str:
    md = re.sub(r"(?m)^(?:\*\*)?(0?\d{1,2})(?:\*\*)?\n\n\*\*([^*\n]{1,80})\*\*$", r"## \1 \2", md)

    def clean_heading(match: re.Match[str]) -> str:
        marker = match.group("marker")
        text = match.group("text").replace("**", "").replace("*", "")
        text = re.sub(r"^(\d+)(?=\S)", r"\1 ", text)
        return f"{marker} {text.strip()}"

    return re.sub(r"(?m)^(?P<marker>#{1,6})\s+(?P<text>.*\*.*)$", clean_heading, md)


def _normalize_markdown_emphasis(md: str) -> str:
    md = _ORPHAN_IMAGE_EMPHASIS_RE.sub(r"\g<image>", md)
    md = _ORPHAN_IMAGE_PREFIX_RE.sub(r"\g<image>", md)
    md = re.sub(
        r"(?m)^[ \t]*\*\*[ \t]*$(?:\r?\n(?:[ \t]*\r?\n)?)?",
        "",
        md,
    )
    previous = None
    while previous != md:
        previous = md
        md = re.sub(r"\*\*([^*\n]+)\*{4,}([^*\n]+)\*\*", r"**\1\2**", md)
    md = re.sub(
        r"(?m)^(?P<prefix>[ \t]*)\*\*(?P<text>[^*\n]+?)\*{4,}[ \t]*$",
        r"\g<prefix>**\g<text>**",
        md,
    )
    md = re.sub(
        r"(?m)(?P<prefix>\*\*[^*\n]+\*\*[^\n*]+)\*{4,}[ \t]*$",
        r"\g<prefix>",
        md,
    )
    md = re.sub(
        r"(?<!\*)\*(?!\*)(?P<before>[^*\n]*?)\*\*(?!\*)"
        r"(?P<after>[^*\n]*?)\*(?!\*)",
        r"*\g<before>\g<after>*",
        md,
    )

    md = _normalize_strong_boundaries(md)

    numbered_link = re.compile(
        r"(?m)^\**(?P<number>\d+\.)\s*\**(?P<link>\[[^\]\n]+\]\([^\n]+\))\**$"
    )
    return numbered_link.sub(r"\g<number> \g<link>", md)


def _normalize_strong_boundaries(md: str) -> str:
    def normalize_strong_span(match: re.Match[str]) -> str:
        text = match.group("text")
        before = match.string[match.start() - 1] if match.start() else ""
        after = match.string[match.end()] if match.end() < len(match.string) else ""
        has_text_before = _is_text_character(before)
        has_text_after = _is_text_character(after)

        if not any(_is_text_character(character) for character in text) and (
            has_text_before or has_text_after
        ):
            return text

        closing = _PAIRED_PUNCTUATION.get(text[:1])
        if (
            closing
            and text.endswith(closing)
            and len(text) > 2
            and (has_text_before or has_text_after)
        ):
            return f"{text[0]}**{text[1:-1]}**{closing}"

        if has_text_after:
            for opening, closing in _TRAILING_GROUP_PAIRS:
                if not text.endswith(closing):
                    continue
                opening_index = text.rfind(opening)
                if opening_index <= 0 or opening_index >= len(text) - 2:
                    continue
                prefix_with_spacing = text[:opening_index]
                prefix = prefix_with_spacing.rstrip()
                if not prefix:
                    continue
                spacing = prefix_with_spacing[len(prefix) :]
                nested = text[opening_index + 1 : -1]
                return f"**{prefix}**{spacing}{opening}**{nested}**{closing}"

        if has_text_before and _is_punctuation(text[0]):
            prefix_length = 0
            while prefix_length < len(text) and _is_punctuation(text[prefix_length]):
                prefix_length += 1
            prefix = text[:prefix_length]
            body = text[prefix_length:]
            if body:
                return f"{prefix}**{body}**"
            return text

        if has_text_after and text[-1] in _STRONG_BOUNDARY_PUNCTUATION:
            return f"**{text}** "

        if has_text_after and _is_punctuation(text[-1]):
            suffix_start = len(text)
            while suffix_start > 0 and _is_punctuation(text[suffix_start - 1]):
                suffix_start -= 1
            body = text[:suffix_start]
            suffix = text[suffix_start:]
            if body:
                return f"**{body}**{suffix}"

        return match.group(0)

    def normalize_prose(segment: str) -> str:
        segment = re.sub(
            rf"{_STRONG_OPEN}(?P<text>[^*\n]*?\S)[ \t]+\*\*",
            r"**\g<text>**",
            segment,
        )
        segment = re.sub(
            r"(?<!\*)\*{4,}(?P<text>[^*\n]+?)\*{4,}(?!\*)",
            r"**\g<text>**",
            segment,
        )
        return _STRONG_SPAN_RE.sub(normalize_strong_span, segment)

    def normalize_segment(segment: str) -> str:
        parts: list[str] = []
        cursor = 0
        for match in _INLINE_CODE_RE.finditer(segment):
            parts.append(normalize_prose(segment[cursor : match.start()]))
            parts.append(match.group(0))
            cursor = match.end()
        parts.append(normalize_prose(segment[cursor:]))
        return "".join(parts)

    parts: list[str] = []
    cursor = 0
    for match in _FENCED_CODE_BLOCK_RE.finditer(md):
        parts.append(normalize_segment(md[cursor : match.start()]))
        parts.append(match.group(0))
        cursor = match.end()
    parts.append(normalize_segment(md[cursor:]))
    return "".join(parts)


def _split_fenced_segments(md: str) -> list[tuple[bool, str]]:
    segments: list[tuple[bool, str]] = []
    current_lines: list[str] = []
    in_fence = False
    fence_character = ""
    fence_length = 0

    def flush(is_code: bool) -> None:
        if current_lines:
            segments.append((is_code, "".join(current_lines)))
            current_lines.clear()

    for line in md.splitlines(keepends=True):
        line_text = line.rstrip("\r\n")
        match = _FENCE_LINE_RE.match(line_text)
        if not in_fence:
            if match:
                flush(False)
                in_fence = True
                fence = match.group("fence")
                fence_character = fence[0]
                fence_length = len(fence)
            current_lines.append(line)
            continue

        current_lines.append(line)
        if not match:
            continue
        fence = match.group("fence")
        if (
            fence[0] == fence_character
            and len(fence) >= fence_length
            and not match.group("tail").strip()
        ):
            flush(True)
            in_fence = False
            fence_character = ""
            fence_length = 0

    flush(in_fence)
    return segments


def _transform_prose(md: str, transform: Callable[[str], str]) -> str:
    def transform_inline_aware(segment: str) -> str:
        parts: list[str] = []
        cursor = 0
        for match in _INLINE_CODE_RE.finditer(segment):
            parts.append(transform(segment[cursor : match.start()]))
            parts.append(match.group(0))
            cursor = match.end()
        parts.append(transform(segment[cursor:]))
        return "".join(parts)

    return "".join(
        segment if is_code else transform_inline_aware(segment)
        for is_code, segment in _split_fenced_segments(md)
    )


def _repair_paired_escaped_strong(md: str) -> str:
    return _transform_prose(
        md,
        lambda segment: _PAIRED_ESCAPED_STRONG_RE.sub(
            r"**\g<text>**",
            segment,
        ),
    )


def _repair_address_only_fences(md: str) -> str:
    parts: list[str] = []
    for is_code, segment in _split_fenced_segments(md):
        if not is_code:
            parts.append(segment)
            continue
        match = _ADDRESS_ONLY_FENCE_RE.fullmatch(segment)
        if not match:
            parts.append(segment)
            continue
        parts.append(
            f"{match.group('label')}<{match.group('url')}>"
            f"{match.group('terminal')}{match.group('ending') or ''}"
        )
    return "".join(parts)


def repair_markdown_quality(md: str) -> str:
    md = _repair_address_only_fences(md)
    md = md.replace("\u00a0", " ")
    md = _repair_paired_escaped_strong(md)
    md = _transform_prose(md, _strip_image_emphasis)
    md = _transform_prose(md, _separate_markdown_images)
    md = _transform_prose(md, _normalize_markdown_emphasis)
    md = _transform_prose(
        md,
        lambda segment: re.sub(r"\n{4,}", "\n\n\n", segment),
    )
    return md


def _remove_code_widget_noise(md: str) -> str:
    md = re.sub(r"(?:[ce]?ounter\(line\)?)+", "", md)
    md = re.sub(r"(?:一键获取完整项目代码|AI写代码)(?:[a-zA-Z]+)?", "", md)
    md = re.sub(r"(?m)^[a-zA-Z0-9_+-]*复制代码", "", md)
    md = re.sub(r"```[a-zA-Z0-9_-]*\n[ \t]*```\n?", "", md)
    return md


def _first_list_item_text_node(element: Tag) -> tuple[NavigableString | None, bool]:
    for child in element.children:
        if isinstance(child, NavigableString):
            if child.strip():
                return child, False
            continue
        if not isinstance(child, Tag):
            continue
        if child.name in _LIST_MARKER_PROTECTED_ELEMENTS:
            return None, True
        text_node, blocked = _first_list_item_text_node(child)
        if text_node is not None or blocked:
            return text_node, blocked
    return None, False


def _strip_redundant_list_markers(content_html: str) -> str:
    soup = BeautifulSoup(content_html, "html.parser")
    for unordered_list in soup.find_all("ul"):
        for list_item in unordered_list.find_all("li", recursive=False):
            text_node, _blocked = _first_list_item_text_node(list_item)
            if text_node is None:
                continue
            cleaned_text = _UNORDERED_LIST_BULLET_RE.sub("", str(text_node), count=1)
            if cleaned_text != str(text_node):
                text_node.replace_with(cleaned_text)

    for ordered_list in soup.find_all("ol"):
        expected_number = _html_integer_attribute(ordered_list, "start", 1)
        for list_item in ordered_list.find_all("li", recursive=False):
            item_number = _html_integer_attribute(list_item, "value", expected_number)
            text_node, _blocked = _first_list_item_text_node(list_item)
            if text_node is not None:
                match = _ORDERED_LIST_NUMBER_RE.match(str(text_node))
                if match is not None and int(match.group("number")) == item_number:
                    text_node.replace_with(str(text_node)[match.end() :])
            expected_number = item_number + 1
    return str(soup)


def _html_integer_attribute(element: Tag, attribute: str, default: int) -> int:
    try:
        return int(str(element.get(attribute, default)))
    except (TypeError, ValueError):
        return default


def html_to_markdown(content_html: str, code_blocks: list[dict[str, str]] | None = None) -> str:
    content_html = _strip_redundant_list_markers(content_html)
    md = markdownify.markdownify(
        content_html,
        heading_style="ATX",
        bullets="-",
        convert=[
            "p",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "strong",
            "em",
            "a",
            "img",
            "ul",
            "ol",
            "li",
            "blockquote",
            "br",
            "hr",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "pre",
            "code",
        ],
    )
    md = md.replace("\u00a0", " ")
    md = _transform_prose(md, _strip_image_emphasis)
    md = _transform_prose(md, _normalize_bare_urls)
    for block in code_blocks or []:
        if "raw_html" in block:
            md = md.replace(block["placeholder"], f"\n{block['raw_html']}\n")
            continue
        fence = f"\n```{block['lang']}\n{block['code']}\n```\n"
        md = md.replace(block["placeholder"], fence)
    md = _remove_code_widget_noise(md)
    md = _transform_prose(md, _separate_markdown_images)
    md = _transform_prose(md, _promote_numbered_markdown_headings)
    md = _transform_prose(md, _normalize_markdown_emphasis)
    md = _transform_prose(
        md,
        lambda segment: re.sub(r"\n{4,}", "\n\n\n", segment),
    )
    md = _transform_prose(
        md,
        lambda segment: re.sub(r"[ \t]+$", "", segment, flags=re.MULTILINE),
    )
    return md.strip()
