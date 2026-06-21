from __future__ import annotations

import re

import markdownify


_FENCED_CODE_BLOCK_RE = re.compile(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$")
_STRONG_BOUNDARY_PUNCTUATION = r":："
_STRONG_FOLLOWING_TEXT = r"A-Za-z0-9_\u4e00-\u9fff"
_STRONG_PRECEDING_TEXT = r"\w\u4e00-\u9fff"
_STRONG_OPEN = rf"(?<![{_STRONG_PRECEDING_TEXT}])\*\*(?![ \t*])"


def _separate_markdown_images(md: str) -> str:
    image = r"!\[[^\]]*\]\([^)\n]+\)"
    md = re.sub(r"!\[\]\(\)", "", md)
    md = re.sub(rf"([^\[\n])({image})", r"\1\n\n\2", md)
    md = re.sub(rf"({image})([^\]\n])", r"\1\n\n\2", md)
    md = re.sub(rf"({image})\s*({image})", r"\1\n\n\2", md)
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
    previous = None
    while previous != md:
        previous = md
        md = re.sub(r"\*\*([^*\n]+)\*{4,}([^*\n]+)\*\*", r"**\1\2**", md)

    md = _normalize_strong_boundaries(md)

    numbered_link = re.compile(
        r"(?m)^\**(?P<number>\d+\.)\s*\**(?P<link>\[[^\]\n]+\]\([^\n]+\))\**$"
    )
    return numbered_link.sub(r"\g<number> \g<link>", md)


def _normalize_strong_boundaries(md: str) -> str:
    def normalize_segment(segment: str) -> str:
        segment = re.sub(
            rf"{_STRONG_OPEN}(?P<text>[^*\n]*?\S)[ \t]+\*\*",
            r"**\g<text>**",
            segment,
        )
        return re.sub(
            rf"(?P<strong>{_STRONG_OPEN}[^*\n]*[{_STRONG_BOUNDARY_PUNCTUATION}]\*\*)"
            rf"(?P<next>[{_STRONG_FOLLOWING_TEXT}])",
            r"\g<strong> \g<next>",
            segment,
        )

    parts: list[str] = []
    cursor = 0
    for match in _FENCED_CODE_BLOCK_RE.finditer(md):
        parts.append(normalize_segment(md[cursor : match.start()]))
        parts.append(match.group(0))
        cursor = match.end()
    parts.append(normalize_segment(md[cursor:]))
    return "".join(parts)


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
