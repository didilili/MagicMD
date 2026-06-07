from __future__ import annotations


class MagicMDError(Exception):
    """Base class for public MagicMD SDK errors."""

    def __init__(self, message: str, *, stage: str = "convert"):
        self.stage = stage
        super().__init__(message)


class UnsupportedPlatformError(MagicMDError):
    """Raised when a requested platform is not supported by MagicMD."""


class FetchError(MagicMDError):
    """Raised when MagicMD cannot fetch the article HTML."""


class ParseError(MagicMDError):
    """Raised when MagicMD cannot parse fetched HTML into an article."""


class MediaDownloadError(MagicMDError):
    """Raised when media download fails before a package can be finalized."""


class ConversionError(MagicMDError):
    """Raised when MagicMD cannot render or write the conversion result."""
