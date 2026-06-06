from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import markdownify
from bs4 import BeautifulSoup, Tag

from pagemd.models import ImageAsset


def normalize_text(value: str) -> str:
    lines = [" ".join(line.split()) for line in (value or "").splitlines()]
    return "\n".join(line for line in lines if line).strip()


def meta_content(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return normalize_text(str(tag["content"]))
    return ""


def unix_to_shanghai_iso(value: str) -> str:
    if not value or not value.isdigit():
        return ""
    tz = timezone(timedelta(hours=8))
    return datetime.fromtimestamp(int(value), tz=tz).isoformat()


def extract_script_value(html: str, name: str) -> str:
    patterns = [
        rf"var\s+{re.escape(name)}\s*=\s*['\"](?P<value>.*?)['\"]",
        rf"{re.escape(name)}\s*[:=]\s*['\"]?(?P<value>\d+)['\"]?",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.S)
        if match:
            return normalize_text(match.group("value"))
    return ""


def clean_content_element(content_el: Tag) -> tuple[str, list[ImageAsset], list[dict[str, str]]]:
    for selector in ("script", "style", "nav", "footer", ".qr_code_pc", ".reward_area"):
        for tag in content_el.select(selector):
            tag.decompose()

    for img in content_el.find_all("img"):
        data_src = img.get("data-src")
        if data_src:
            img["src"] = data_src

    images: list[ImageAsset] = []
    seen: set[str] = set()
    for img in content_el.find_all("img"):
        src = img.get("src")
        if not src or src in seen:
            continue
        seen.add(src)
        images.append(ImageAsset(source_url=src, alt=img.get("alt", "")))

    code_blocks: list[dict[str, str]] = []
    for index, el in enumerate(content_el.select(".code-snippet__fix")):
        for line_idx in el.select(".code-snippet__line-index"):
            line_idx.decompose()
        pre = el.select_one("pre[data-lang]")
        lang = pre.get("data-lang", "") if pre else ""
        lines = []
        for code_tag in el.find_all("code"):
            text = code_tag.get_text()
            if re.match(r"^[ce]?ounter\(line", text):
                continue
            lines.append(text)
        code = "\n".join(lines) or el.get_text()
        placeholder = f"PAGEMDCODEBLOCK{index}"
        code_blocks.append({"placeholder": placeholder, "lang": lang, "code": code})
        el.replace_with(placeholder)

    return str(content_el), images, code_blocks


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
        fence = f"\n```{block['lang']}\n{block['code']}\n```\n"
        md = md.replace(block["placeholder"], fence)
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    md = re.sub(r"[ \t]+$", "", md, flags=re.MULTILINE)
    return md.strip()
