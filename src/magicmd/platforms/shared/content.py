from __future__ import annotations

import re
import textwrap
from collections.abc import Callable
from collections import Counter
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

from magicmd.models import ImageAsset
from magicmd.platforms.shared.metadata import normalize_text


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
    block_names = {
        "blockquote",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "ul",
    }
    return any(isinstance(child, Tag) and child.name in block_names for child in tag.children)


def _is_bold_style(style: str) -> bool:
    weight = _style_value(style, "font-weight")
    return weight == "bold" or (weight.isdigit() and int(weight) >= 600)


def _is_italic_style(style: str) -> bool:
    return _style_value(style, "font-style") in {"italic", "oblique"}


def _has_visible_background(style: str) -> bool:
    value = _style_value(style, "background-color") or _style_value(style, "background")
    normalized = re.sub(r"\s+", "", value)
    return bool(
        normalized
        and normalized
        not in {
            "none",
            "transparent",
            "rgba(0,0,0,0)",
            "rgba(0,0,0,0.0)",
        }
    )


def _heading_level_from_style(style: str, *, semantically_bold: bool = False) -> int | None:
    font_size = _style_font_size(style)
    is_bold = semantically_bold or _is_bold_style(style)
    if font_size >= 24:
        return 2
    if font_size >= 20 and (is_bold or _has_heading_color(style)):
        return 2
    if is_bold and font_size >= 17:
        return 3
    return None


def _is_semantically_bold_within(tag: Tag, boundary: Tag) -> bool:
    current: Tag | None = tag
    while current is not None:
        if current.name in {"strong", "b"} or _is_bold_style(current.get("style", "")):
            return True
        if current is boundary or not isinstance(current.parent, Tag):
            return False
        current = current.parent
    return False


def _visual_heading_level(tag: Tag) -> int | None:
    text = normalize_text(tag.get_text(" ", strip=True))
    if not text or len(text) > 90:
        return None

    own_style = tag.get("style", "")
    styles = [(own_style, _is_bold_style(own_style))]
    if not _style_font_size(own_style) and isinstance(tag.parent, Tag):
        parent_style = tag.parent.get("style", "")
        styles.append((parent_style, _is_bold_style(parent_style)))
    for descendant in tag.find_all(["span", "strong", "b", "em"]):
        descendant_text = normalize_text(descendant.get_text(" ", strip=True))
        style = descendant.get("style", "")
        if (
            descendant_text == text
            and _style_font_size(style)
            and not _has_visible_background(style)
        ):
            styles.append((style, _is_semantically_bold_within(descendant, tag)))

    levels = [
        level
        for style, semantically_bold in styles
        if (
            level := _heading_level_from_style(
                style,
                semantically_bold=semantically_bold,
            )
        )
    ]
    return min(levels, default=None)


def _looks_like_heading(tag: Tag) -> bool:
    return _visual_heading_level(tag) is not None


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
            if classes.intersection(
                {
                    "js_mpvedio",
                    "mp-video-player",
                    "page_video_wrapper",
                    "page_video",
                    "video_iframe",
                }
            ):
                container = ancestor
        for descendant in container.descendants:
            if isinstance(descendant, Tag):
                seen.add(id(descendant))
        media = (
            container
            if container.name in {"video", "iframe", "mp-video"}
            else container.find(["video", "iframe", "mp-video"])
        )
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
    parent = img.parent
    if (
        0 < natural_width <= 32
        and {"rich_pages", "wxw-img"}.issubset(classes)
        and not normalize_text(str(img.get("alt") or ""))
        and img.find_parent("a") is None
        and isinstance(parent, Tag)
        and not normalize_text(parent.get_text(" ", strip=True))
    ):
        parent_style = parent.get("style", "")
        parent_width = _style_pixel_value(parent_style, "width")
        parent_height = _style_pixel_value(parent_style, "height")
        if 0 < parent_width <= 32 and 0 < parent_height <= 32:
            return True
    if "__bg_gif" in classes and classes.intersection(placeholder_classes) and 0 < width <= 32:
        return True
    if _is_in_poster_template(img) and natural_width >= 250 and 0 < ratio <= 0.13:
        return True
    if (
        _is_in_poster_template(img)
        and natural_width >= 500
        and 0.18 <= ratio <= 0.35
        and str(img.get("data-type") or "").lower() != "gif"
        and _is_followed_by_poster_heading_text(img)
    ):
        return True
    if "wx_img_placeholder_mini" in classes and natural_width >= 900 and 0.7 <= ratio <= 1.2:
        return True
    if width <= 32 and natural_width >= 900 and 0.7 <= ratio <= 1.2:
        return True
    return False


def _is_in_poster_template(img: Tag) -> bool:
    for ancestor in img.parents:
        if not isinstance(ancestor, Tag):
            continue
        background = _style_value(ancestor.get("style", ""), "background-color")
        if background and not _is_body_color(background):
            return True
    return False


def _is_followed_by_poster_heading_text(img: Tag) -> bool:
    for element in img.find_all_next():
        if not isinstance(element, Tag):
            continue
        if element.name == "img":
            return False
        text = normalize_text(element.get_text(" ", strip=True))
        if not text:
            continue
        return len(text) <= 40 and _element_or_descendant_looks_like_heading(element)
    return False


def _element_or_descendant_looks_like_heading(element: Tag) -> bool:
    if _looks_like_heading(element):
        return True
    for descendant in element.find_all(["section", "p", "span"]):
        if normalize_text(descendant.get_text(" ", strip=True)) and _looks_like_heading(descendant):
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
            if _is_link_color(span.get("style", ""))
            and normalize_text(span.get_text(" ", strip=True))
        ]
        linked_text = normalize_text(
            " ".join(span.get_text(" ", strip=True) for span in link_spans)
        )
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


def _h1_uses_body_text_style(tag: Tag) -> bool:
    styled_elements = [*tag.find_all(["span", "strong", "em"]), tag]
    for element in styled_elements:
        if not normalize_text(element.get_text(" ", strip=True)):
            continue
        style = element.get("style", "")
        font_size = _style_font_size(style)
        if not font_size:
            continue
        color = _style_value(style, "color")
        return (
            font_size <= 16 and not _is_bold_style(style) and (not color or _is_body_color(color))
        )
    return False


def _is_layout_heading(tag: Tag) -> bool:
    if tag.name not in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        return False
    if tag.find("img"):
        return True
    if tag.name == "h1":
        return _h1_uses_body_text_style(tag)

    style = tag.get("style", "")
    font_size = _style_font_size(style)
    layout_style = any(
        token in style.lower() for token in ("background-color", "padding", "margin")
    )
    if tag.name in {"h4", "h5", "h6"} and layout_style and font_size <= 16:
        return True

    color = _style_value(style, "color")
    if tag.name in {"h3", "h4", "h5", "h6"} and layout_style and color and _is_body_color(color):
        return True

    classes = set(tag.get("class", []))
    is_wechat_layout = any(str(class_name).startswith("js_darkmode") for class_name in classes)
    if (
        tag.name in {"h3", "h4", "h5", "h6"}
        and is_wechat_layout
        and color
        and _is_body_color(color)
    ):
        return True
    return False


def _normalize_layout_headings(content_el: Tag) -> None:
    for tag in content_el.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if _is_layout_heading(tag):
            tag.name = "p"


def _is_centered(tag: Tag) -> bool:
    return _style_value(tag.get("style", ""), "text-align").split()[0:1] == ["center"]


def _is_newzhiyuan_chapter_mark(img: Tag) -> bool:
    classes = set(img.get("class", []))
    try:
        natural_width = int(float(str(img.get("data-w") or "0")))
        ratio = float(str(img.get("data-ratio") or "0"))
    except ValueError:
        return False

    alt = normalize_text(str(img.get("alt") or ""))
    return (
        natural_width == 112
        and 0.52 <= ratio <= 0.54
        and {"rich_pages", "wxw-img"}.issubset(classes)
        and alt.lower() in {"", "image"}
        and img.find_parent("a") is None
    )


def _newzhiyuan_chapter_mark_container(img: Tag, content_el: Tag) -> Tag | None:
    for ancestor in img.parents:
        if not isinstance(ancestor, Tag) or ancestor is content_el:
            break
        sourced_images = [
            image for image in ancestor.find_all("img") if image.get("src") or image.get("data-src")
        ]
        if (
            ancestor.name in {"div", "p", "section"}
            and _is_centered(ancestor)
            and not normalize_text(ancestor.get_text(" ", strip=True))
            and len(sourced_images) == 1
            and sourced_images[0] is img
        ):
            return ancestor
    return None


def _is_newzhiyuan_chapter_heading_line(tag: Tag) -> bool:
    if tag.name not in {"p", "section"} or not _is_centered(tag):
        return False
    text = normalize_text(tag.get_text(" ", strip=True))
    if not text or len(text) > 60 or _has_visible_background(tag.get("style", "")):
        return False

    for styled in tag.find_all(["span", "strong", "b"]):
        if normalize_text(styled.get_text(" ", strip=True)) != text:
            continue
        font_size = _style_font_size(styled.get("style", ""))
        if not 18.5 <= font_size <= 19.5 or _has_visible_background(styled.get("style", "")):
            continue
        if styled.name in {"strong", "b"} or styled.find(["strong", "b"]):
            return True
    return False


def _join_visual_heading_lines(lines: list[str]) -> str:
    heading = lines[0]
    for line in lines[1:]:
        separator = " " if heading[-1:].isascii() and line[:1].isascii() else ""
        heading += separator + line
    return heading


def _is_empty_heading(tag: Tag | None) -> bool:
    return bool(
        isinstance(tag, Tag)
        and tag.name in {"h1", "h2", "h3", "h4", "h5", "h6"}
        and not normalize_text(tag.get_text(" ", strip=True))
    )


def _normalize_newzhiyuan_chapter_headings(content_el: Tag) -> None:
    for img in list(content_el.find_all("img")):
        if img.parent is None or not _is_newzhiyuan_chapter_mark(img):
            continue
        container = _newzhiyuan_chapter_mark_container(img, content_el)
        if container is None:
            continue

        heading_lines: list[Tag] = []
        sibling = container.find_next_sibling()
        while (
            isinstance(sibling, Tag)
            and len(heading_lines) < 2
            and _is_newzhiyuan_chapter_heading_line(sibling)
        ):
            heading_lines.append(sibling)
            sibling = sibling.find_next_sibling()
        if not heading_lines:
            continue

        heading_text = _join_visual_heading_lines(
            [normalize_text(line.get_text(" ", strip=True)) for line in heading_lines]
        )
        heading = heading_lines[0]
        heading.name = "h2"
        heading.clear()
        heading.append(NavigableString(heading_text))
        for extra_line in heading_lines[1:]:
            extra_line.decompose()
        preceding = container.find_previous_sibling()
        if isinstance(preceding, Tag) and _is_empty_heading(preceding):
            preceding.decompose()
        container.decompose()

        following = heading.find_next_sibling()
        if isinstance(following, Tag) and _is_empty_heading(following):
            following.decompose()


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
        if level := _visual_heading_level(tag):
            tag.name = f"h{level}"
        else:
            tag.name = "p"


def _remove_empty_headings(content_el: Tag) -> None:
    for tag in list(content_el.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])):
        if _is_empty_heading(tag):
            tag.decompose()


def _flatten_nested_emphasis(content_el: Tag) -> None:
    for outer in content_el.find_all(["strong", "em"]):
        for nested in list(outer.find_all(outer.name)):
            nested.unwrap()


def _looks_like_direct_url(value: str) -> bool:
    return bool(re.match(r"^(?:https?://|mailto:|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/)", value.strip()))


def _direct_link_target(link: Tag) -> str:
    title = normalize_text(str(link.get("title") or ""))
    if _looks_like_direct_url(title):
        return title
    href = str(link.get("href") or "")
    parsed = urlparse(href)
    if parsed.netloc.endswith("link.juejin.cn"):
        target = parse_qs(parsed.query).get("target", [""])[0]
        target = unquote(target)
        if _looks_like_direct_url(target):
            return target
    return ""


def _normalize_external_links(content_el: Tag) -> None:
    for link in content_el.find_all("a"):
        direct_target = _direct_link_target(link)
        if not direct_target:
            continue
        link["href"] = direct_target
        if link.get("title") == direct_target:
            del link["title"]
        text = normalize_text(link.get_text(" ", strip=True))
        if "..." in text or "…" in text:
            link.clear()
            link.append(NavigableString(direct_target))


def _remove_code_chrome(content_el: Tag) -> None:
    selectors = [
        ".opt-box",
        ".hide-preCode-box",
        ".pre-numbering",
        ".hljs-button",
        ".btn-code-notes",
        ".look-more-preCode",
    ]
    for tag in content_el.select(",".join(selectors)):
        tag.decompose()


def _block_placeholder(kind: str, index: int) -> str:
    return f"MAGICMD{kind.upper()}BLOCK{index:06d}END"


def _scrollable_text_block_content(tag: Tag) -> str:
    paragraphs = tag.find_all("p")
    if not paragraphs:
        return ""

    lines: list[str] = []
    for paragraph in paragraphs:
        for line_break in paragraph.find_all("br"):
            line_break.replace_with(NavigableString("\n"))
        text = paragraph.get_text("", strip=False)
        text = text.replace("\u00a0", " ").replace("\r\n", "\n").replace("\r", "\n")
        lines.append(text.strip())
    return "\n".join(lines).strip("\n")


def _preserve_scrollable_text_blocks(content_el: Tag, blocks: list[dict[str, str]]) -> None:
    excluded_content = ["audio", "code", "iframe", "img", "pre", "svg", "table", "video"]
    for tag in list(content_el.find_all(["div", "section"])):
        style = str(tag.get("style") or "")
        overflow_y = _style_value(style, "overflow-y")
        fixed_height = _style_pixel_value(style, "height") or _style_pixel_value(
            style, "max-height"
        )
        if not re.match(r"^(?:auto|scroll)(?:\s*!important)?$", overflow_y) or not fixed_height:
            continue
        if not tag.find(attrs={"data-autoskip": True}) or tag.find(excluded_content):
            continue

        text = _scrollable_text_block_content(tag)
        if not text:
            continue
        placeholder = _block_placeholder("code", len(blocks))
        blocks.append(
            {
                "placeholder": placeholder,
                "lang": "text",
                "code": text,
                "normalize_block_spacing": "true",
            }
        )
        tag.replace_with(NavigableString(placeholder))


def _preserve_raw_html_blocks(content_el: Tag, blocks: list[dict[str, str]]) -> None:
    for tag in list(content_el.select(".mermaid")):
        if not tag.find("svg"):
            continue
        for script in tag.find_all("script"):
            script.decompose()
        placeholder = _block_placeholder("html", len(blocks))
        blocks.append({"placeholder": placeholder, "raw_html": str(tag)})
        tag.replace_with(NavigableString(placeholder))


def _normalize_body_heading_depth(content_el: Tag) -> None:
    headings = [
        tag
        for tag in content_el.find_all(re.compile(r"^h[1-6]$"))
        if isinstance(tag, Tag) and normalize_text(tag.get_text(" ", strip=True))
    ]
    if not headings:
        return

    levels = [int(str(tag.name)[1]) for tag in headings]
    min_level = min(levels)
    base_level = min_level
    counts = Counter(levels)
    dominant_level, dominant_count = counts.most_common(1)[0]
    dominant_headings = [tag for tag in headings if int(str(tag.name)[1]) == dominant_level]
    numbered_count = sum(
        1
        for tag in dominant_headings
        if re.match(r"^\d+(?:[.)、]|\s)", normalize_text(tag.get_text(" ", strip=True)))
    )

    if (
        dominant_level > min_level
        and dominant_count >= 3
        and dominant_count / len(headings) >= 0.6
        and numbered_count / dominant_count >= 0.5
    ):
        base_level = dominant_level

    heading_stack: list[tuple[int, int]] = []
    for tag in headings:
        source_level = max(base_level, int(str(tag.name)[1]))
        while heading_stack and heading_stack[-1][0] >= source_level:
            heading_stack.pop()

        normalized_level = 2 if not heading_stack else min(6, heading_stack[-1][1] + 1)
        tag.name = f"h{normalized_level}"
        heading_stack.append((source_level, normalized_level))


def _transform_unquoted_text(text: str, transform: Callable[[str], str]) -> str:
    parts: list[str] = []
    segment_start = 0
    quote_start = 0
    quote = ""
    escaped = False

    for index, character in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                parts.append(text[quote_start : index + 1])
                segment_start = index + 1
                quote = ""
            continue

        if character not in {'"', "'", "`"}:
            continue
        preceding_backslashes = 0
        cursor = index - 1
        while cursor >= 0 and text[cursor] == "\\":
            preceding_backslashes += 1
            cursor -= 1
        if preceding_backslashes % 2:
            continue
        parts.append(transform(text[segment_start:index]))
        quote_start = index
        quote = character

    if quote:
        parts.append(text[quote_start:])
    else:
        parts.append(transform(text[segment_start:]))
    return "".join(parts)


def _normalize_code_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    starters = (
        "conda",
        "pip3",
        "pip",
        "docker",
        "kubectl",
        "npm",
        "yarn",
        "pnpm",
        "sudo",
        "print",
        "import",
    )

    def normalize_unquoted(segment: str) -> str:
        safe_prose_boundary = r"\u3400-\u9fff，。！？；：、,;:!?"
        segment = re.sub(
            rf"(?<=[{safe_prose_boundary}])(?=(?:{'|'.join(starters)})[ \t])",
            "\n",
            segment,
        )
        segment = re.sub(r"(?<=\d)(?=conda[ \t])", "\n", segment)
        return re.sub(r"(?<=\))(?=print\()", "\n", segment)

    return _transform_unquoted_text(text, normalize_unquoted)


def _code_text(code_tag: Tag) -> str:
    highlighted_lines = code_tag.select(".hljs-ln-code .hljs-ln-line")
    if highlighted_lines:
        lines = [
            _normalize_code_text(line.get_text("", strip=False)).rstrip()
            for line in highlighted_lines
        ]
        return textwrap.dedent("\n".join(lines)).strip("\n")
    text = "".join(
        "\n"
        if isinstance(descendant, Tag) and descendant.name == "br"
        else str(descendant)
        if isinstance(descendant, NavigableString)
        else ""
        for descendant in code_tag.descendants
    )
    return _normalize_code_text(text)


def clean_content_element(content_el: Tag) -> tuple[str, list[ImageAsset], list[dict[str, str]]]:
    code_blocks: list[dict[str, str]] = []
    _preserve_raw_html_blocks(content_el, code_blocks)

    for selector in ("script", "style", "nav", "footer", ".qr_code_pc", ".reward_area"):
        for tag in content_el.select(selector):
            tag.decompose()

    _replace_video_players(content_el)
    _normalize_non_code_pre(content_el)
    _normalize_newzhiyuan_chapter_headings(content_el)
    _normalize_layout_headings(content_el)
    _narrow_block_links(content_el)
    _normalize_external_links(content_el)
    _remove_code_chrome(content_el)
    _preserve_scrollable_text_blocks(content_el, code_blocks)

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
    _remove_empty_headings(content_el)
    _flatten_nested_emphasis(content_el)
    _normalize_body_heading_depth(content_el)

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

    for index, el in enumerate(content_el.select(".code-snippet__fix")):
        for line_idx in el.select(".code-snippet__line-index"):
            line_idx.decompose()
        pre = el.select_one("pre[data-lang]")
        lang = pre.get("data-lang", "") if pre else ""
        lines = []
        for code_tag in el.find_all("code"):
            text = _code_text(code_tag)
            if re.match(r"^[ce]?ounter\(line", text):
                continue
            lines.append(text)
        code = "\n".join(lines) or el.get_text()
        placeholder = _block_placeholder("code", len(code_blocks))
        code_blocks.append({"placeholder": placeholder, "lang": lang, "code": code})
        el.replace_with(placeholder)

    for el in list(content_el.find_all("pre")):
        if el.find_parent(".code-snippet__fix"):
            continue
        code_tag = el.find("code", recursive=False)
        if not isinstance(code_tag, Tag):
            continue
        code = _code_text(code_tag)
        if not code.strip():
            continue
        lang = str(el.get("data-lang") or "")
        if not lang:
            classes = [str(class_name) for class_name in code_tag.get("class", [])]
            lang = next(
                (
                    class_name.removeprefix("language-")
                    for class_name in classes
                    if class_name.startswith("language-")
                ),
                "",
            )
        placeholder = _block_placeholder("code", len(code_blocks))
        code_blocks.append({"placeholder": placeholder, "lang": lang, "code": code})
        el.replace_with(placeholder)

    return str(content_el), images, code_blocks
