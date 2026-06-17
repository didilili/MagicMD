from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field

from magicmd.platforms.registry import platform_adapters


class OutputNamingConfig(BaseModel):
    package: str = "{date}-{slug}"
    markdown: str = "article.md"
    metadata: str = "metadata.json"
    report: str = "extraction-report.json"
    docx: str = "article.docx"


class OutputConfig(BaseModel):
    directory: str = "output"
    overwrite: bool = False
    save_debug_html: str = "on_failure"
    naming: OutputNamingConfig = Field(default_factory=OutputNamingConfig)


class MarkdownConfig(BaseModel):
    template: str = "default"
    preset: str = "default"
    front_matter: str = "yaml"
    include_title: bool = True
    include_source_block: bool = True
    heading_offset: int = 0
    source_block_template: str = (
        "> Source: {platform}\n> Author: {author}\n> Original: {source_url}"
    )
    front_matter_fields: dict[str, str] = Field(
        default_factory=lambda: {
            "title": "{title}",
            "author": "{author}",
            "platform": "{platform}",
            "source_url": "{source_url}",
            "published_at": "{published_at}",
        }
    )


class ImagesConfig(BaseModel):
    download: bool = True
    directory: str = "images"
    filename_pattern: str = "img_{index:03d}.{ext}"
    markdown_path: str = "{directory}/{filename}"
    concurrency: int = 5


class VideosConfig(BaseModel):
    download: bool = True
    directory: str = "videos"
    filename_pattern: str = "video_{index:03d}.{ext}"
    markdown_path: str = "{directory}/{filename}"


class DocxConfig(BaseModel):
    enabled: bool = False
    pandoc_path: str = "pandoc"
    reference_doc: str = ""


class FetchConfig(BaseModel):
    timeout_seconds: int = 20
    browser_timeout_seconds: int = 15
    browser_attempts: int = 2
    user_agent: str = "default"


class UiConfig(BaseModel):
    language: str = "zh-CN"


class PlatformConfig(BaseModel):
    enabled: bool = True
    browser: str = "http"
    wait_selector: str = ""


class MagicMDConfig(BaseModel):
    output: OutputConfig = Field(default_factory=OutputConfig)
    markdown: MarkdownConfig = Field(default_factory=MarkdownConfig)
    images: ImagesConfig = Field(default_factory=ImagesConfig)
    videos: VideosConfig = Field(default_factory=VideosConfig)
    docx: DocxConfig = Field(default_factory=DocxConfig)
    fetch: FetchConfig = Field(default_factory=FetchConfig)
    ui: UiConfig = Field(default_factory=UiConfig)
    platforms: dict[str, PlatformConfig] = Field(
        default_factory=lambda: {
            adapter.name: PlatformConfig(
                browser=adapter.default_browser,
                wait_selector=adapter.default_wait_selector,
            )
            for adapter in platform_adapters()
        }
    )


def _deep_merge(base: dict, override: dict, path: tuple[str, ...] = ()) -> dict:
    merged = dict(base)
    for key, value in override.items():
        next_path = (*path, key)
        if next_path == ("markdown", "front_matter_fields"):
            merged[key] = value
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value, next_path)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = None) -> MagicMDConfig:
    from magicmd.presets import apply_preset

    default = MagicMDConfig().model_dump()
    if not path:
        return apply_preset(MagicMDConfig.model_validate(default))
    config_path = Path(path)
    if not config_path.exists():
        return apply_preset(MagicMDConfig.model_validate(default))
    loaded = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return apply_preset(MagicMDConfig.model_validate(_deep_merge(default, loaded)), loaded)
