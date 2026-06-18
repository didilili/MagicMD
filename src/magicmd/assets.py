from __future__ import annotations

from collections.abc import Callable
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


def download_videos(
    article: Article,
    package_dir: Path,
    video_dir_name: str = "videos",
    filename_pattern: str = "video_{index:03d}.{ext}",
    markdown_path_pattern: str = "{directory}/{filename}",
) -> Article:
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
                    filename = filename_pattern.format(index=len(seen) + 1, ext=ext)
                    saved_path = video_dir / filename
                    local_path = markdown_path_pattern.format(
                        directory=video_dir_name,
                        filename=filename,
                        index=len(seen) + 1,
                        ext=ext,
                    )
                    saved_path.write_bytes(response.content)
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
    markdown_path_pattern: str = "{directory}/{filename}",
) -> Article:
    if not article.images and not article.cover_image and not article.share_cover_image:
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
        for image in article.images:
            saved_index = len(next_images) + 1

            def filename_from_pattern(ext: str, index: int = saved_index) -> str:
                return filename_pattern.format(index=index, ext=ext)

            next_images.append(
                _download_image_asset(
                    client,
                    image,
                    article,
                    image_dir,
                    image_dir_name,
                    filename_from_pattern,
                    markdown_path_pattern,
                    warnings,
                    local_path_index=saved_index,
                )
            )
        cover_local_path_index = len(next_images) + 1
        share_cover_local_path_index = cover_local_path_index + (1 if article.cover_image else 0)
        cover_image = _download_image_asset(
            client,
            article.cover_image,
            article,
            image_dir,
            image_dir_name,
            lambda ext: f"cover.{ext}",
            markdown_path_pattern,
            warnings,
            local_path_index=cover_local_path_index,
            warning_prefix="cover_image_download_failed",
        )
        share_cover_image = _download_image_asset(
            client,
            article.share_cover_image,
            article,
            image_dir,
            image_dir_name,
            lambda ext: f"share_cover.{ext}",
            markdown_path_pattern,
            warnings,
            local_path_index=share_cover_local_path_index,
            warning_prefix="share_cover_image_download_failed",
        )
    next_article = article.model_copy(
        update={
            "cover_image": cover_image,
            "share_cover_image": share_cover_image,
            "images": next_images,
        }
    )
    if next_images:
        next_article.content_markdown = rewrite_markdown_image_links(
            next_article.content_markdown, next_images
        )
    next_article.extraction.warnings = warnings
    return next_article


def _download_image_asset(
    client: httpx.Client,
    image: ImageAsset | None,
    article: Article,
    image_dir: Path,
    image_dir_name: str,
    filename_builder: Callable[[str], str],
    markdown_path_pattern: str,
    warnings: list[str],
    local_path_index: int,
    warning_prefix: str = "image_download_failed",
) -> ImageAsset | None:
    if image is None:
        return None
    url = image.source_url if not image.source_url.startswith("//") else f"https:{image.source_url}"
    try:
        response = client.get(url, headers={"Referer": article.source_url})
        response.raise_for_status()
        ext = infer_image_extension(url, response.headers.get("content-type", ""))
        filename = filename_builder(ext)
        saved_path = image_dir / filename
        local_path = markdown_path_pattern.format(
            directory=image_dir_name,
            filename=filename,
            index=local_path_index,
            ext=ext,
        )
        saved_path.write_bytes(response.content)
        return image.model_copy(update={"local_path": local_path})
    except Exception as exc:
        warnings.append(f"{warning_prefix}:{url}:{exc}")
        return image
