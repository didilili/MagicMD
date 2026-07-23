from __future__ import annotations

from collections.abc import Callable
import re
import unicodedata

import markdownify


_FENCED_CODE_BLOCK_RE = re.compile(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$")
_INLINE_CODE_RE = re.compile(r"(`+)([^\n]*?)\1")
_ADDRESS_ONLY_FENCE_RE = re.compile(
    r"(?m)^(?P<fence>`{3,}|~{3,})[^\n]*\n"
    r"(?P<label>[ \t]*(?:开源地址|项目地址|官网)[ \t]*[：:][ \t]*)"
    r"(?P<url>https?://[^\s<>\n]+)[ \t]*\n"
    r"(?P=fence)[ \t]*$"
)
_PAIRED_ESCAPED_STRONG_RE = re.compile(
    r"\\\*\\\*(?P<text>[^\\*\n](?:.*?[^\\*\n])?)\\\*\\\*"
)
_BARE_URL_RE = re.compile(
    r"(?<![<(])(?P<url>https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+)"
    r"(?=[，。！？；：、\u4e00-\u9fff])"
)
_ORPHAN_IMAGE_EMPHASIS_RE = re.compile(
    r"(?m)^[ \t]*\*\*[ \t]*\r?\n"
    r"(?:[ \t]*\r?\n)*"
    r"(?P<image>!\[[^\]]*\]\([^)\n]*\))[ \t]*\r?\n"
    r"(?:[ \t]*\r?\n)*"
    r"[ \t]*\*\*[ \t]*$"
)
_ORPHAN_IMAGE_PREFIX_RE = re.compile(
    r"(?m)^[ \t]*\*\*[ \t]*\r?\n"
    r"(?:[ \t]*\r?\n)*"
    r"(?P<image>!\[[^\]]*\]\([^)\n]*\))[ \t]*$"
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


def _is_punctuation(value: str) -> bool:
    return bool(value) and unicodedata.category(value).startswith("P")


def _is_text_character(value: str) -> bool:
    if not value:
        return False
    category = unicodedata.category(value)
    return value == "_" or category.startswith(("L", "N"))


def _strip_image_emphasis(md: str) -> str:
    image = r"!\[[^\]]*\]\([^)\n]*\)"
    return re.sub(
        rf"(?<!\*)\*{{1,3}}(?P<image>{image})\*{{1,3}}(?!\*)",
        r"\g<image>",
        md,
    )


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
    image = r"!\[[^\]]*\]\([^)\n]+\)"
    md, empty_image_count = re.subn(r"!\[[^\]]*\]\(\s*\)", "", md)
    md = re.sub(rf"([^\[\n])({image})", r"\1\n\n\2", md)
    md = re.sub(rf"({image})([^\]\n])", r"\1\n\n\2", md)
    md = re.sub(rf"({image})\s*({image})", r"\1\n\n\2", md)
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

        if (
            not any(_is_text_character(character) for character in text)
            and (has_text_before or has_text_after)
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
                prefix = text[:opening_index]
                nested = text[opening_index + 1 : -1]
                return f"**{prefix}**{opening}**{nested}**{closing}"

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

    parts: list[str] = []
    cursor = 0
    for match in _FENCED_CODE_BLOCK_RE.finditer(md):
        parts.append(transform_inline_aware(md[cursor : match.start()]))
        parts.append(match.group(0))
        cursor = match.end()
    parts.append(transform_inline_aware(md[cursor:]))
    return "".join(parts)


def _repair_paired_escaped_strong(md: str) -> str:
    return _transform_prose(
        md,
        lambda segment: _PAIRED_ESCAPED_STRONG_RE.sub(
            r"**\g<text>**",
            segment,
        ),
    )


def _repair_address_only_fences(md: str) -> str:
    return _ADDRESS_ONLY_FENCE_RE.sub(r"\g<label><\g<url>>", md)


def repair_markdown_quality(md: str) -> str:
    md = _repair_address_only_fences(md)
    md = md.replace("\u00a0", " ")
    md = _repair_paired_escaped_strong(md)
    md = _transform_prose(md, _normalize_markdown_emphasis)
    md = _separate_markdown_images(md)
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    return md


def _remove_code_widget_noise(md: str) -> str:
    md = re.sub(r"(?:[ce]?ounter\(line\)?)+", "", md)
    md = re.sub(r"(?:一键获取完整项目代码|AI写代码)(?:[a-zA-Z]+)?", "", md)
    md = re.sub(r"(?m)^[a-zA-Z0-9_+-]*复制代码", "", md)
    md = re.sub(r"```[a-zA-Z0-9_-]*\n[ \t]*```\n?", "", md)
    return md


def html_to_markdown(content_html: str, code_blocks: list[dict[str, str]] | None = None) -> str:
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
    md = _strip_image_emphasis(md)
    md = _normalize_bare_urls(md)
    for block in code_blocks or []:
        if "raw_html" in block:
            md = md.replace(block["placeholder"], f"\n{block['raw_html']}\n")
            continue
        fence = f"\n```{block['lang']}\n{block['code']}\n```\n"
        md = md.replace(block["placeholder"], fence)
    md = _remove_code_widget_noise(md)
    md = _separate_markdown_images(md)
    md = _promote_numbered_markdown_headings(md)
    md = _normalize_markdown_emphasis(md)
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    md = re.sub(r"[ \t]+$", "", md, flags=re.MULTILINE)
    return md.strip()
