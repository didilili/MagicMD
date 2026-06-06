from __future__ import annotations

from pydantic import BaseModel, Field


class ImageAsset(BaseModel):
    source_url: str
    local_path: str = ""
    alt: str = ""


class ExtractionInfo(BaseModel):
    status: str = "success"
    platform: str
    parser: str
    warnings: list[str] = Field(default_factory=list)


class Article(BaseModel):
    title: str
    author: str = ""
    platform: str
    source_url: str
    canonical_url: str = ""
    published_at: str = ""
    excerpt: str = ""
    language: str = "zh-CN"
    content_markdown: str = ""
    content_html: str = ""
    content_hash: str = ""
    images: list[ImageAsset] = Field(default_factory=list)
    extraction: ExtractionInfo

    def to_metadata(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "platform": self.platform,
            "source_url": self.source_url,
            "canonical_url": self.canonical_url or self.source_url,
            "published_at": self.published_at,
            "excerpt": self.excerpt,
            "language": self.language,
            "content_hash": self.content_hash,
            "images": [image.model_dump() for image in self.images],
            "extraction": self.extraction.model_dump(),
        }

