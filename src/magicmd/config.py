from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field

from magicmd.platforms.registry import platform_adapters


class OutputConfig(BaseModel):
    directory: str = "output"
    overwrite: bool = False
    save_debug_html: str = "on_failure"


class MarkdownConfig(BaseModel):
    template: str = "default"
    front_matter: str = "yaml"
    include_source_block: bool = True
    heading_offset: int = 0


class ImagesConfig(BaseModel):
    download: bool = True
    directory: str = "images"
    filename_pattern: str = "img_{index:03d}.{ext}"
    concurrency: int = 5


class FetchConfig(BaseModel):
    timeout_seconds: int = 20
    browser_timeout_seconds: int = 15
    browser_attempts: int = 2
    user_agent: str = "default"


class PlatformConfig(BaseModel):
    enabled: bool = True
    browser: str = "http"
    wait_selector: str = ""


class MagicMDConfig(BaseModel):
    output: OutputConfig = Field(default_factory=OutputConfig)
    markdown: MarkdownConfig = Field(default_factory=MarkdownConfig)
    images: ImagesConfig = Field(default_factory=ImagesConfig)
    fetch: FetchConfig = Field(default_factory=FetchConfig)
    platforms: dict[str, PlatformConfig] = Field(
        default_factory=lambda: {
            adapter.name: PlatformConfig(
                browser=adapter.default_browser,
                wait_selector=adapter.default_wait_selector,
            )
            for adapter in platform_adapters()
        }
    )


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = None) -> MagicMDConfig:
    default = MagicMDConfig().model_dump()
    if not path:
        return MagicMDConfig.model_validate(default)
    config_path = Path(path)
    if not config_path.exists():
        return MagicMDConfig.model_validate(default)
    loaded = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return MagicMDConfig.model_validate(_deep_merge(default, loaded))
