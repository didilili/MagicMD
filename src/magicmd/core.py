"""Offline conversion APIs. These functions never fetch URLs or write files."""

from magicmd.detect import detect_platform
from magicmd.exceptions import UnsupportedPlatformError
from magicmd.models import Article
from magicmd.platforms.registry import get_platform_adapter, platform_names
from magicmd.platforms.shared.markdown import repair_markdown_quality


def parse_html(html: str, url: str, platform: str = "auto") -> Article:
    """Parse caller-supplied HTML; the caller owns fetching, limits and storage."""
    resolved = detect_platform(url) if platform == "auto" else platform
    try:
        adapter = get_platform_adapter(resolved)
    except KeyError as exc:
        supported = ", ".join(platform_names())
        raise UnsupportedPlatformError(
            f"Unsupported platform: {resolved}. Supported platforms: {supported}", stage="detect"
        ) from exc
    return adapter.parser(html, url)


def repair_markdown(markdown: str) -> str:
    """Repair prose formatting while preserving fenced and inline code."""
    return repair_markdown_quality(markdown)
