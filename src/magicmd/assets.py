from __future__ import annotations

import re
from pathlib import Path

import httpx

from magicmd.models import Article, ImageAsset


def infer_image_extension(url: str, content_type: str = "") -> str:
    match = re.search(r"wx_fmt=(\w+)", url) or re.search(r"\.(\w{3,4})(?:\?|$)", url)
    if match:
        ext = match.group(1).lower().replace("jpeg", "jpg")
        if ext != "other":
            return ext
    if "jpeg" in content_type:
        return "jpg"
    if "png" in content_type:
        return "png"
    if "gif" in content_type:
        return "gif"
    if "webp" in content_type:
        return "webp"
    return "png"


def _separate_markdown_images(markdown: str) -> str:
    image = r"!\[[^\]]*\]\([^)\n]+\)"
    markdown = re.sub(r"!\[\]\(\)", "", markdown)
    markdown = re.sub(rf"([^\[\n])({image})", r"\1\n\n\2", markdown)
    markdown = re.sub(rf"({image})([^\]\n])", r"\1\n\n\2", markdown)
    markdown = re.sub(rf"({image})\s*({image})", r"\1\n\n\2", markdown)
    return re.sub(r"\n{4,}", "\n\n\n", markdown).strip()


def rewrite_markdown_image_links(markdown: str, images: list[ImageAsset]) -> str:
    result = markdown
    for image in images:
        if not image.local_path:
            continue
        pattern = re.compile(r"!\[([^\]]*)\]\(" + re.escape(image.source_url) + r"\)")
        result = pattern.sub(lambda match: f"![{match.group(1)}]({image.local_path})", result)
    return _separate_markdown_images(result)


def _video_transport():
    return None


def _image_transport():
    return None


def _unescape_markdown_url(url: str) -> str:
    return re.sub(r"\\([_&=?.:/+\-])", r"\1", url)


def _infer_video_extension(url: str, content_type: str = "") -> str:
    match = re.search(r"\.(mp4|mov|webm|m4v)(?:\?|$)", url, re.I)
    if match:
        return match.group(1).lower()
    if "webm" in content_type:
        return "webm"
    if "quicktime" in content_type:
        return "mov"
    return "mp4"


def download_videos(article: Article, package_dir: Path, video_dir_name: str = "videos") -> Article:
    matches = list(re.finditer(r"\[视频\]\((https?://[^)\n]+)\)", article.content_markdown))
    if not matches:
        return article

    video_dir = package_dir / video_dir_name
    video_dir.mkdir(parents=True, exist_ok=True)
    markdown = article.content_markdown
    warnings = list(article.extraction.warnings)
    seen: dict[str, str] = {}
    transport = _video_transport()
    client_kwargs = {"timeout": 30.0, "follow_redirects": True}
    if transport is not None:
        client_kwargs["transport"] = transport

    with httpx.Client(**client_kwargs) as client:
        for match in matches:
            markdown_url = match.group(1)
            url = _unescape_markdown_url(markdown_url)
            if url not in seen:
                try:
                    response = client.get(
                        url,
                        headers={
                            "Referer": article.source_url,
                            "User-Agent": "Mozilla/5.0 MagicMD",
                            "Accept": "video/mp4,video/*,*/*",
                        },
                    )
                    response.raise_for_status()
                    ext = _infer_video_extension(url, response.headers.get("content-type", ""))
                    local_path = f"{video_dir_name}/video_{len(seen) + 1:03d}.{ext}"
                    (package_dir / local_path).write_bytes(response.content)
                    seen[url] = local_path
                except Exception as exc:
                    warnings.append(f"video_download_failed:{url}:{exc}")
                    seen[url] = url
            markdown = markdown.replace(f"[视频]({markdown_url})", f"[视频]({seen[url]})")

    next_article = article.model_copy(update={"content_markdown": markdown})
    next_article.extraction.warnings = warnings
    return next_article


def download_images(
    article: Article,
    package_dir: Path,
    image_dir_name: str = "images",
    filename_pattern: str = "img_{index:03d}.{ext}",
) -> Article:
    if not article.images:
        return article
    image_dir = package_dir / image_dir_name
    image_dir.mkdir(parents=True, exist_ok=True)
    next_images: list[ImageAsset] = []
    warnings = list(article.extraction.warnings)
    transport = _image_transport()
    client_kwargs = {"timeout": 20.0, "follow_redirects": True}
    if transport is not None:
        client_kwargs["transport"] = transport
    with httpx.Client(**client_kwargs) as client:
        for index, image in enumerate(article.images, start=1):
            url = image.source_url if not image.source_url.startswith("//") else f"https:{image.source_url}"
            try:
                response = client.get(url, headers={"Referer": article.source_url})
                response.raise_for_status()
                ext = infer_image_extension(url, response.headers.get("content-type", ""))
                filename = filename_pattern.format(index=index, ext=ext)
                local_path = f"{image_dir_name}/{filename}"
                (package_dir / local_path).write_bytes(response.content)
                next_images.append(image.model_copy(update={"local_path": local_path}))
            except Exception as exc:
                warnings.append(f"image_download_failed:{url}:{exc}")
                next_images.append(image)
    next_article = article.model_copy(update={"images": next_images})
    next_article.content_markdown = rewrite_markdown_image_links(
        next_article.content_markdown, next_images
    )
    next_article.extraction.warnings = warnings
    return next_article
