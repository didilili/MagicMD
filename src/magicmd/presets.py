from __future__ import annotations

from magicmd.config import MagicMDConfig, _deep_merge


def apply_preset(config: MagicMDConfig, overrides: dict | None = None) -> MagicMDConfig:
    preset = config.markdown.preset
    updates: dict = {}
    if preset == "plain":
        updates = {
            "markdown": {"front_matter": "none", "include_source_block": False},
        }
    elif preset == "hugo":
        updates = {
            "output": {"naming": {"markdown": "index.md"}},
            "markdown": {"front_matter": "yaml", "include_source_block": True},
        }
    elif preset == "docusaurus":
        updates = {
            "output": {"naming": {"markdown": "index.md"}},
            "markdown": {"front_matter": "yaml", "include_source_block": False},
            "images": {"markdown_path": "./{directory}/{filename}"},
        }
    elif preset != "default":
        raise ValueError(f"Unknown markdown preset: {preset}")
    merged = _deep_merge(config.model_dump(), updates)
    if overrides:
        merged = _deep_merge(merged, overrides)
    return MagicMDConfig.model_validate(merged)
