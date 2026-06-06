from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import markdownify
from bs4 import BeautifulSoup, NavigableString, Tag

from magicmd.models import ImageAsset


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


def _style_value(style: str, name: str) -> str:
    match = re.search(rf"(?:^|;)\s*{re.escape(name)}\s*:\s*([^;]+)", style or "", re.I)
    return match.group(1).strip().lower() if match else ""


def _style_font_size(style: str) -> float:
    value = _style_value(style, "font-size")
    match = re.search(r"(\d+(?:\.\d+)?)px", value)
    return float(match.group(1)) if match else 0.0


def _has_heading_color(style: str) -> bool:
    color = _style_value(style, "color")
    if not color:
        return False
    normalized = re.sub(r"\s+", "", color)
    return not _is_body_color(normalized)


def _is_body_color(color: str) -> bool:
    normalized = re.sub(r"\s+", "", color)
    body_colors = {
        "rgb(0,0,0)",
        "rgba(0,0,0,0.9)",
        "rgb(15,15,15)",
        "rgb(34,34,34)",
        "rgb(42,42,42)",
        "rgb(51,51,51)",
        "rgb(62,62,62)",
        "#000",
        "#000000",
        "#222",
        "#222222",
        "#333",
        "#333333",
    }
    return normalized in body_colors


def _style_pixel_value(style: str, name: str) -> float:
    value = _style_value(style, name)
    match = re.search(r"(\d+(?:\.\d+)?)px", value)
    return float(match.group(1)) if match else 0.0


def _style_rgb_tuple(style: str, name: str) -> tuple[int, int, int] | None:
    value = _style_value(style, name)
    match = re.search(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", value)
    if not match:
        return None
    return tuple(int(match.group(index)) for index in range(1, 4))


def _is_link_color(style: str) -> bool:
    rgb = _style_rgb_tuple(style, "color")
    if not rgb:
        return False
    red, green, blue = rgb
    return blue >= 150 and blue > red + 40 and blue > green + 20


def _has_direct_block_child(tag: Tag) -> bool:
    block_names = {"blockquote", "div", "h1", "h2", "h3", "h4", "h5", "h6", "ol", "p", "pre", "section", "table", "ul"}
    return any(isinstance(child, Tag) and child.name in block_names for child in tag.children)


def _is_bold_style(style: str) -> bool:
    weight = _style_value(style, "font-weight")
    return weight == "bold" or (weight.isdigit() and int(weight) >= 600)


def _is_italic_style(style: str) -> bool:
    return _style_value(style, "font-style") in {"italic", "oblique"}


def _looks_like_heading(tag: Tag) -> bool:
    text = normalize_text(tag.get_text(" ", strip=True))
    if not text or len(text) > 90:
        return False
    style = tag.get("style", "")
    font_size = _style_font_size(style)
    if font_size >= 24:
        return True
    if font_size >= 20 and (_is_bold_style(style) or _has_heading_color(style)):
        return True
    if _is_bold_style(style) and font_size >= 17:
        return True
    return False


def _wrap_contents(tag: Tag, wrapper_name: str) -> None:
    if tag.name == wrapper_name or tag.find_parent(wrapper_name):
        return
    wrapper = BeautifulSoup("", "html.parser").new_tag(wrapper_name)
    for child in list(tag.contents):
        wrapper.append(child.extract())
    tag.append(wrapper)


def _replace_video_players(content_el: Tag) -> None:
    selectors = [
        ".js_mpvedio",
        ".mp-video-player",
        ".page_video_wrapper",
        ".page_video",
        ".video_iframe",
        "mp-video",
        "iframe.video_iframe",
        "video",
    ]
    seen: set[int] = set()
    for tag in list(content_el.select(",".join(selectors))):
        if id(tag) in seen or tag.parent is None:
            continue
        container = tag
        for ancestor in tag.parents:
            if not isinstance(ancestor, Tag) or ancestor is content_el:
                break
            classes = set(ancestor.get("class", []))
            if classes.intersection({"js_mpvedio", "mp-video-player", "page_video_wrapper", "page_video", "video_iframe"}):
                container = ancestor
        for descendant in container.descendants:
            if isinstance(descendant, Tag):
                seen.add(id(descendant))
        media = container if container.name in {"video", "iframe", "mp-video"} else container.find(["video", "iframe", "mp-video"])
        src = ""
        if isinstance(media, Tag):
            src = media.get("src") or media.get("data-src") or media.get("data-mpvid") or ""
        text = f"[视频]({src})" if src else "[视频] 原文包含视频，未能提取视频链接。"
        replacement = BeautifulSoup("", "html.parser").new_tag("p")
        replacement.append(NavigableString(text))
        container.replace_with(replacement)


def _is_decorative_image(img: Tag) -> bool:
    classes = set(img.get("class", []))
    placeholder_classes = {"js_img_placeholder", "wx_img_placeholder", "wx_img_placeholder_mini"}
    data_w = img.get("data-w")
    data_ratio = img.get("data-ratio")
    try:
        natural_width = int(float(data_w)) if data_w else 0
    except ValueError:
        natural_width = 0
    try:
        ratio = float(data_ratio) if data_ratio else 0.0
    except ValueError:
        ratio = 0.0
    width = _style_pixel_value(img.get("style", ""), "width")
    if "__bg_gif" in classes and classes.intersection(placeholder_classes) and 0 < width <= 32:
        return True
    if "wx_img_placeholder_mini" in classes and natural_width >= 900 and 0.7 <= ratio <= 1.2:
        return True
    if width <= 32 and natural_width >= 900 and 0.7 <= ratio <= 1.2:
        return True
    return False


def _narrow_block_links(content_el: Tag) -> None:
    for link in list(content_el.find_all("a")):
        href = link.get("href")
        if not href or not link.find(["div", "p", "section"]):
            continue
        full_text = normalize_text(link.get_text(" ", strip=True))
        if not full_text:
            continue
        link_spans = [
            span
            for span in link.find_all("span")
            if _is_link_color(span.get("style", "")) and normalize_text(span.get_text(" ", strip=True))
        ]
        linked_text = normalize_text(" ".join(span.get_text(" ", strip=True) for span in link_spans))
        if not linked_text or len(linked_text) >= len(full_text) * 0.8:
            continue
        for span in link_spans:
            scoped_link = BeautifulSoup("", "html.parser").new_tag("a", href=href)
            if link.get("title"):
                scoped_link["title"] = link["title"]
            span.wrap(scoped_link)
        link.unwrap()


def _normalize_non_code_pre(content_el: Tag) -> None:
    for pre in content_el.find_all("pre"):
        if pre.find("code") or pre.find_parent(".code-snippet__fix"):
            continue
        pre.name = "section"


def _is_layout_heading(tag: Tag) -> bool:
    if tag.name not in {"h2", "h3", "h4", "h5", "h6"}:
        return False
    if tag.find("img"):
        return True

    style = tag.get("style", "")
    font_size = _style_font_size(style)
    layout_style = any(token in style.lower() for token in ("background-color", "padding", "margin"))
    if tag.name in {"h4", "h5", "h6"} and layout_style and font_size <= 16:
        return True

    color = _style_value(style, "color")
    if tag.name in {"h3", "h4", "h5", "h6"} and layout_style and color and _is_body_color(color):
        return True

    classes = set(tag.get("class", []))
    is_wechat_layout = any(str(class_name).startswith("js_darkmode") for class_name in classes)
    if tag.name in {"h3", "h4", "h5", "h6"} and is_wechat_layout and color and _is_body_color(color):
        return True
    return False


def _normalize_layout_headings(content_el: Tag) -> None:
    for tag in content_el.find_all(["h2", "h3", "h4", "h5", "h6"]):
        if _is_layout_heading(tag):
            tag.name = "p"


def _normalize_wechat_rich_text(content_el: Tag) -> None:
    for tag in content_el.find_all(["span", "em"]):
        style = tag.get("style", "")
        if _is_bold_style(style):
            _wrap_contents(tag, "strong")
        if _is_italic_style(style):
            _wrap_contents(tag, "em")

    for tag in reversed(content_el.find_all(["section", "p"])):
        if not isinstance(tag, Tag) or _has_direct_block_child(tag):
            continue
        if _looks_like_heading(tag):
            tag.name = "h2"
        else:
            tag.name = "p"


def clean_content_element(content_el: Tag) -> tuple[str, list[ImageAsset], list[dict[str, str]]]:
    for selector in ("script", "style", "nav", "footer", ".qr_code_pc", ".reward_area"):
        for tag in content_el.select(selector):
            tag.decompose()

    _replace_video_players(content_el)
    _normalize_non_code_pre(content_el)
    _normalize_layout_headings(content_el)
    _narrow_block_links(content_el)

    for img in content_el.find_all("img"):
        data_src = img.get("data-src")
        if data_src:
            img["src"] = data_src
        if not img.get("src") or _is_decorative_image(img):
            img.decompose()
            continue
        if not img.get("alt"):
            img["alt"] = "Image"

    _normalize_wechat_rich_text(content_el)

    for img in content_el.find_all("img"):
        if not img.get("src"):
            img.decompose()

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
        placeholder = f"MAGICMDCODEBLOCK{index}"
        code_blocks.append({"placeholder": placeholder, "lang": lang, "code": code})
        el.replace_with(placeholder)

    return str(content_el), images, code_blocks


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

    numbered_link = re.compile(
        r"(?m)^\**(?P<number>\d+\.)\s*\**(?P<link>\[[^\]\n]+\]\([^\n]+\))\**$"
    )
    return numbered_link.sub(r"\g<number> \g<link>", md)


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
    md = _separate_markdown_images(md)
    md = _promote_numbered_markdown_headings(md)
    md = _normalize_markdown_emphasis(md)
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    md = re.sub(r"[ \t]+$", "", md, flags=re.MULTILINE)
    return md.strip()
