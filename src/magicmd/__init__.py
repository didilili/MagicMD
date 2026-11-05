__version__ = "0.8.0"

from magicmd.exceptions import (
    ConversionError,
    FetchError,
    MagicMDError,
    MediaDownloadError,
    ParseError,
    UnsupportedPlatformError,
)
from magicmd.core import parse_html, repair_markdown


def __getattr__(name: str):
    if name in {"ArticleConversionResult", "ConvertedImage", "ConvertedVideo", "convert_article"}:
        from magicmd import sdk

        value = getattr(sdk, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ArticleConversionResult",
    "ConvertedImage",
    "ConvertedVideo",
    "ConversionError",
    "FetchError",
    "MagicMDError",
    "MediaDownloadError",
    "ParseError",
    "UnsupportedPlatformError",
    "__version__",
    "convert_article",
    "parse_html",
    "repair_markdown",
]
