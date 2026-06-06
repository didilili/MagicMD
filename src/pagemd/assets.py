from __future__ import annotations

import re
from pathlib import Path

import httpx

from pagemd.models import Article, ImageAsset


def infer_image_extension(url: str, content_type: str = "") -> str:
    match = re.search(r"wx_fmt=(\w+)", url) or re.search(r"\.(\w{3,4})(?:\?|$)", url)
    if match:
        return match.group(1).lower().replace("jpeg", "jpg")
    if "jpeg" in content_type:
        return "jpg"
    if "png" in content_type:
        return "png"
    if "gif" in content_type:
        return "gif"
    if "webp" in content_type:
        return "webp"
    return "png"


def rewrite_markdown_image_links(markdown: str, images: list[ImageAsset]) -> str:
    result = markdown
    for image in images:
        if not image.local_path:
            continue
        pattern = re.compile(r"!\[([^\]]*)\]\(" + re.escape(image.source_url) + r"\)")
        result = pattern.sub(lambda match: f"![{match.group(1)}]({image.local_path})", result)
    return result


def download_images(article: Article, package_dir: Path, image_dir_name: str = "images") -> Article:
    if not article.images:
        return article
    image_dir = package_dir / image_dir_name
    image_dir.mkdir(parents=True, exist_ok=True)
    next_images: list[ImageAsset] = []
    warnings = list(article.extraction.warnings)
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        for index, image in enumerate(article.images, start=1):
            url = image.source_url if not image.source_url.startswith("//") else f"https:{image.source_url}"
            try:
                response = client.get(url, headers={"Referer": article.source_url})
                response.raise_for_status()
                ext = infer_image_extension(url, response.headers.get("content-type", ""))
                local_path = f"{image_dir_name}/img_{index:03d}.{ext}"
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

