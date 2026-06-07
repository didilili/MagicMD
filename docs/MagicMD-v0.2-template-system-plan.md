# MagicMD v0.2 Template System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users control package names, output filenames, Markdown front matter, source blocks, media paths, and publishing presets from `.magicmd.toml` without changing code.

**Architecture:** Extend the existing Pydantic config model first, then move naming and Markdown rendering into small focused helpers. Keep defaults compatible with v0.1.x: existing users still get `article.md`, `metadata.json`, `extraction-report.json`, `images/img_001.png`, and package directories like `{date}-{slug}`.

**Tech Stack:** Python 3.11, Pydantic config models, TOML config via `tomllib`, Typer CLI, pytest.

---

## Why v0.2

MagicMD already converts WeChat, Juejin, CSDN, and generic public articles into Markdown packages. The next useful step is not another platform adapter; it is making the output fit the user's publishing system.

Target users should be able to configure:

- Package directory names.
- Markdown file names such as `article.md`, `index.md`, or `{slug}.md`.
- Metadata and extraction report file names.
- Image and video directory names.
- Front matter fields.
- Source information block.
- Presets for `default`, `plain`, `hugo`, `hexo`, and `docusaurus`.

## Current State

Already configurable:

- `output.directory`
- `output.overwrite`
- `output.save_debug_html`
- `markdown.template`
- `markdown.front_matter`
- `markdown.include_source_block`
- `markdown.heading_offset`
- `images.download`
- `images.directory`
- `images.filename_pattern`
- `fetch.*`
- `platforms.*`

Currently hardcoded:

- Package directory pattern in `src/magicmd/output.py`.
- Markdown filename `article.md`.
- Metadata filename `metadata.json`.
- Extraction report filename `extraction-report.json`.
- Video directory `videos`.
- Front matter field list in `src/magicmd/renderers/markdown.py`.
- Source block shape in `src/magicmd/renderers/markdown.py`.

## Target Config

```toml
[output]
directory = "output"
overwrite = false
save_debug_html = "on_failure"

[output.naming]
package = "{date}-{slug}"
markdown = "article.md"
metadata = "metadata.json"
report = "extraction-report.json"

[markdown]
preset = "default"
front_matter = "yaml"
include_title = true
include_source_block = true
heading_offset = 0
source_block_template = """
> Source: {platform}
> Author: {author}
> Original: {source_url}
"""

[markdown.front_matter_fields]
title = "{title}"
date = "{published_at}"
author = "{author}"
platform = "{platform}"
source_url = "{source_url}"

[images]
download = true
directory = "images"
filename_pattern = "img_{index:03d}.{ext}"
markdown_path = "{directory}/{filename}"
concurrency = 5

[videos]
download = true
directory = "videos"
filename_pattern = "video_{index:03d}.{ext}"
markdown_path = "{directory}/{filename}"

[presets.hugo]
markdown = "index.md"
front_matter = "yaml"
include_source_block = true
image_markdown_path = "{directory}/{filename}"

[presets.docusaurus]
markdown = "index.md"
front_matter = "yaml"
include_source_block = false
image_markdown_path = "./{directory}/{filename}"
```

## Template Variables

All templates should use Python format-style fields and fail with a clear message if an unknown field is used.

Required variables:

- `{title}`
- `{slug}`
- `{date}`: first 10 characters of `published_at`, or `undated`
- `{published_at}`
- `{author}`
- `{platform}`
- `{source_url}`
- `{canonical_url}`
- `{content_hash}`
- `{short_hash}`: first 6 characters of `content_hash`

Media-only variables:

- `{index}`
- `{ext}`
- `{filename}`
- `{directory}`

## File Map

- Modify `src/magicmd/config.py`: add naming, videos, preset, front matter, and template config models.
- Create `src/magicmd/template_vars.py`: build safe template variable dictionaries and format strings.
- Modify `src/magicmd/output.py`: use `output.naming` for package and file names.
- Modify `src/magicmd/diagnostics.py`: write extraction reports using configured report filename.
- Modify `src/magicmd/assets.py`: add video config and markdown path template support.
- Modify `src/magicmd/renderers/markdown.py`: render configurable front matter and source block.
- Modify `src/magicmd/cli.py`: pass full config to output, report, and media functions.
- Modify `.magicmd.example.toml`: move target v0.2 fields from comments to active fields after implementation.
- Modify `src/magicmd/templates/magicmd.example.toml`: keep packaged config template identical to root example.
- Add tests in `tests/test_config.py`, `tests/test_output.py`, `tests/test_markdown.py`, `tests/test_assets.py`, and `tests/test_cli.py`.

## Task 1: Config Models

**Files:**

- Modify: `src/magicmd/config.py`
- Test: `tests/test_config.py`

- [x] **Step 1: Add failing tests for naming and template config**

Add this test to `tests/test_config.py`:

```python
def test_load_config_accepts_v02_output_and_markdown_templates(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output.naming]
        package = "{date}/{slug}"
        markdown = "index.md"
        metadata = "meta.json"
        report = "report.json"

        [markdown]
        preset = "hugo"
        front_matter = "yaml"
        include_title = false
        source_block_template = "> From: {source_url}"

        [markdown.front_matter_fields]
        title = "{title}"
        url = "{source_url}"

        [videos]
        download = false
        directory = "media/videos"
        filename_pattern = "clip_{index:03d}.{ext}"
        markdown_path = "../videos/{filename}"
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output.naming.package == "{date}/{slug}"
    assert config.output.naming.markdown == "index.md"
    assert config.output.naming.metadata == "meta.json"
    assert config.output.naming.report == "report.json"
    assert config.markdown.preset == "hugo"
    assert config.markdown.include_title is False
    assert config.markdown.source_block_template == "> From: {source_url}"
    assert config.markdown.front_matter_fields == {
        "title": "{title}",
        "url": "{source_url}",
    }
    assert config.videos.download is False
    assert config.videos.directory == "media/videos"
    assert config.videos.filename_pattern == "clip_{index:03d}.{ext}"
    assert config.videos.markdown_path == "../videos/{filename}"
```

- [x] **Step 2: Run the failing test**

Run:

```bash
uv run pytest tests/test_config.py::test_load_config_accepts_v02_output_and_markdown_templates -q
```

Expected: fail because `naming`, `preset`, `include_title`, `front_matter_fields`, and `videos` do not exist yet.

- [x] **Step 3: Implement config models**

Add these models in `src/magicmd/config.py`:

```python
class OutputNamingConfig(BaseModel):
    package: str = "{date}-{slug}"
    markdown: str = "article.md"
    metadata: str = "metadata.json"
    report: str = "extraction-report.json"


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
        "> Source: {platform}\n"
        "> Author: {author}\n"
        "> Original: {source_url}"
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


class VideosConfig(BaseModel):
    download: bool = True
    directory: str = "videos"
    filename_pattern: str = "video_{index:03d}.{ext}"
    markdown_path: str = "{directory}/{filename}"
```

Add `videos: VideosConfig = Field(default_factory=VideosConfig)` to `MagicMDConfig`.

- [x] **Step 4: Run config tests**

Run:

```bash
uv run pytest tests/test_config.py -q
```

Expected: all config tests pass.

## Task 2: Template Variables

**Files:**

- Create: `src/magicmd/template_vars.py`
- Test: `tests/test_template_vars.py`

- [x] **Step 1: Add tests for article and media template variables**

Create `tests/test_template_vars.py`:

```python
import pytest

from magicmd.models import Article, ExtractionInfo
from magicmd.template_vars import build_article_template_vars, format_template


def make_article() -> Article:
    return Article(
        title="Codex 实战",
        author="HaoGit",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        canonical_url="https://example.com/canonical",
        published_at="2026-06-06T12:00:00+08:00",
        content_markdown="正文",
        content_hash="abcdef123456",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )


def test_build_article_template_vars():
    variables = build_article_template_vars(make_article())

    assert variables["title"] == "Codex 实战"
    assert variables["slug"] == "codex-实战"
    assert variables["date"] == "2026-06-06"
    assert variables["short_hash"] == "abcdef"


def test_format_template_raises_clear_error_for_unknown_field():
    with pytest.raises(ValueError, match="Unknown template field: missing"):
        format_template("{missing}", {"title": "demo"})
```

- [x] **Step 2: Run the failing tests**

Run:

```bash
uv run pytest tests/test_template_vars.py -q
```

Expected: fail because `magicmd.template_vars` does not exist.

- [x] **Step 3: Implement template helpers**

Create `src/magicmd/template_vars.py`:

```python
from __future__ import annotations

from collections.abc import Mapping

from magicmd.models import Article
from magicmd.output import slugify_title


class SafeTemplateVars(dict[str, object]):
    def __missing__(self, key: str) -> str:
        raise KeyError(key)


def build_article_template_vars(article: Article) -> dict[str, str]:
    date = article.published_at[:10] if article.published_at else "undated"
    content_hash = article.content_hash or ""
    return {
        "title": article.title,
        "slug": slugify_title(article.title),
        "date": date,
        "published_at": article.published_at,
        "author": article.author,
        "platform": article.platform,
        "source_url": article.source_url,
        "canonical_url": article.canonical_url,
        "content_hash": content_hash,
        "short_hash": content_hash[:6],
    }


def format_template(template: str, variables: Mapping[str, object]) -> str:
    try:
        return template.format_map(SafeTemplateVars(variables))
    except KeyError as exc:
        raise ValueError(f"Unknown template field: {exc.args[0]}") from exc
```

- [x] **Step 4: Run tests**

Run:

```bash
uv run pytest tests/test_template_vars.py -q
```

Expected: pass.

## Task 3: Output Naming

**Files:**

- Modify: `src/magicmd/output.py`
- Test: `tests/test_output.py`

- [x] **Step 1: Add failing output naming test**

Add this test:

```python
from magicmd.config import OutputConfig, OutputNamingConfig


def test_write_article_package_uses_configured_output_names(tmp_path: Path):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-06T12:00:00+08:00",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    output_config = OutputConfig(
        naming=OutputNamingConfig(
            package="{date}/{slug}",
            markdown="index.md",
            metadata="meta.json",
            report="report.json",
        )
    )

    package_dir = write_article_package(article, tmp_path, output_config=output_config)

    assert package_dir == tmp_path / "2026-06-06" / "codex-实战"
    assert (package_dir / "index.md").exists()
    assert (package_dir / "meta.json").exists()
```

- [x] **Step 2: Run the failing test**

Run:

```bash
uv run pytest tests/test_output.py::test_write_article_package_uses_configured_output_names -q
```

Expected: fail because `write_article_package` does not accept `output_config`.

- [x] **Step 3: Implement naming**

Update `write_article_package` and `write_article_files` to accept `output_config: OutputConfig | None`.

Use:

```python
from magicmd.config import MarkdownConfig, OutputConfig
from magicmd.template_vars import build_article_template_vars, format_template
```

Inside `write_article_package`:

```python
config = output_config or OutputConfig()
article = ensure_content_hash(article)
variables = build_article_template_vars(article)
package_dir = base / format_template(config.naming.package, variables)
```

Inside `write_article_files`:

```python
config = output_config or OutputConfig()
(package_path / format_template(config.naming.markdown, variables)).write_text(...)
(package_path / format_template(config.naming.metadata, variables)).write_text(...)
```

- [x] **Step 4: Update existing callers**

In `src/magicmd/cli.py`, pass `output_config=config.output` when calling `write_article_package` and `write_article_files`.

- [x] **Step 5: Run output and CLI tests**

Run:

```bash
uv run pytest tests/test_output.py tests/test_cli.py -q
```

Expected: pass.

## Task 4: Configurable Extraction Report Filename

**Files:**

- Modify: `src/magicmd/diagnostics.py`
- Modify: `src/magicmd/cli.py`
- Test: `tests/test_cli.py`

- [x] **Step 1: Add failing CLI test**

Add a CLI test that writes a config file with:

```toml
[output.naming]
report = "report.json"
```

Run a mocked conversion and assert `report.json` exists.

- [x] **Step 2: Modify save function**

Change `save_extraction_report(package_dir, extraction)` to accept `filename: str = "extraction-report.json"`.

In `convert_url`, call:

```python
save_extraction_report(
    package_dir,
    article.to_metadata()["extraction"],
    format_template(config.output.naming.report, build_article_template_vars(article)),
)
```

- [x] **Step 3: Run CLI tests**

Run:

```bash
uv run pytest tests/test_cli.py -q
```

Expected: pass.

## Task 5: Markdown Front Matter and Source Templates

**Files:**

- Modify: `src/magicmd/renderers/markdown.py`
- Test: `tests/test_markdown.py`

- [x] **Step 1: Add failing Markdown template test**

Add:

```python
from magicmd.config import MarkdownConfig


def test_render_markdown_uses_configured_front_matter_and_source_block():
    article = Article(
        title="Codex 实战",
        author="HaoGit",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-06T12:00:00+08:00",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    config = MarkdownConfig(
        include_title=False,
        front_matter_fields={"title": "{title}", "url": "{source_url}"},
        source_block_template="> Saved from {source_url}",
    )

    md = render_markdown(article, config)

    assert 'title: "Codex 实战"' in md
    assert 'url: "https://mp.weixin.qq.com/s/demo"' in md
    assert "# Codex 实战" not in md
    assert "> Saved from https://mp.weixin.qq.com/s/demo" in md
```

- [x] **Step 2: Run the failing test**

Run:

```bash
uv run pytest tests/test_markdown.py::test_render_markdown_uses_configured_front_matter_and_source_block -q
```

Expected: fail because fields and source template are hardcoded.

- [x] **Step 3: Implement front matter field rendering**

Use `build_article_template_vars` and `format_template`. For YAML values, keep `_quote`.

Render configured fields in insertion order:

```python
for key, value_template in config.front_matter_fields.items():
    lines.append(f"{key}: {_quote(format_template(value_template, variables))}")
```

Only add the H1 when `config.include_title` is true.

Render source block with:

```python
source_block = format_template(config.source_block_template, variables).strip()
```

- [x] **Step 4: Run Markdown tests**

Run:

```bash
uv run pytest tests/test_markdown.py -q
```

Expected: pass.

## Task 6: Media Path Templates

**Files:**

- Modify: `src/magicmd/assets.py`
- Modify: `src/magicmd/cli.py`
- Test: `tests/test_assets.py`

- [x] **Step 1: Add image path template test**

Add a unit test around `download_images` using the existing test transport pattern. Configure:

```python
image_dir_name = "assets/images"
filename_pattern = "cover_{index:02d}.{ext}"
markdown_path = "/static/{directory}/{filename}"
```

Assert Markdown image links become `/static/assets/images/cover_01.png`.

- [x] **Step 2: Modify `download_images` signature**

Add:

```python
markdown_path_pattern: str = "{directory}/{filename}"
```

When a file is saved, compute:

```python
filename = filename_pattern.format(index=index, ext=ext)
local_path = markdown_path_pattern.format(
    directory=image_dir_name,
    filename=filename,
    index=index,
    ext=ext,
)
```

Still write bytes to `package_dir / image_dir_name / filename`.

- [x] **Step 3: Add video config wiring**

Add `video_dir_name`, `filename_pattern`, and `markdown_path_pattern` to `download_videos`.

In `convert_url`, call with `config.videos.*`.

- [x] **Step 4: Run asset tests**

Run:

```bash
uv run pytest tests/test_assets.py -q
```

Expected: pass.

## Task 7: Presets

**Files:**

- Modify: `src/magicmd/config.py`
- Create: `src/magicmd/presets.py`
- Test: `tests/test_config.py`

- [x] **Step 1: Add preset tests**

Add tests asserting:

- `plain` disables front matter and source block.
- `hugo` uses `index.md` and YAML front matter.
- `docusaurus` uses `index.md`, YAML front matter, and `./{directory}/{filename}` image paths.

- [x] **Step 2: Implement preset application**

Create `src/magicmd/presets.py`:

```python
from __future__ import annotations

from magicmd.config import MagicMDConfig


def apply_preset(config: MagicMDConfig) -> MagicMDConfig:
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
    return MagicMDConfig.model_validate(_deep_merge(config.model_dump(), updates))
```

Expose `_deep_merge` or move it to a shared helper. Apply preset after TOML load, before returning config.

- [x] **Step 3: Run config tests**

Run:

```bash
uv run pytest tests/test_config.py -q
```

Expected: pass.

## Task 8: Activate Example Config

**Files:**

- Modify: `.magicmd.example.toml`
- Modify: `src/magicmd/templates/magicmd.example.toml`
- Test: `tests/test_config.py`

- [ ] **Step 1: Move v0.2 fields from comments to active config**

After implementation, make this active:

```toml
[output.naming]
package = "{date}-{slug}"
markdown = "article.md"
metadata = "metadata.json"
report = "extraction-report.json"

[markdown.front_matter_fields]
title = "{title}"
author = "{author}"
platform = "{platform}"
source_url = "{source_url}"
published_at = "{published_at}"

[videos]
download = true
directory = "videos"
filename_pattern = "video_{index:03d}.{ext}"
markdown_path = "{directory}/{filename}"
```

- [ ] **Step 2: Keep root and packaged template identical**

Run:

```bash
diff -u .magicmd.example.toml src/magicmd/templates/magicmd.example.toml
```

Expected: no diff.

- [ ] **Step 3: Update packaged template test**

In `tests/test_config.py`, assert the template contains:

```python
assert "[output.naming]" in template_text
assert 'markdown = "article.md"' in template_text
assert "[markdown.front_matter_fields]" in template_text
assert "[videos]" in template_text
```

## Final Verification

Run:

```bash
uv run pytest
uv run ruff check .
rm -f dist/*.whl dist/*.tar.gz
uv build
uvx twine check dist/*
tmp_dir=$(mktemp -d)
uv venv "$tmp_dir/venv"
uv pip install --python "$tmp_dir/venv/bin/python" dist/magicmd-*.whl
"$tmp_dir/venv/bin/magicmd" --version
"$tmp_dir/venv/bin/magicmd" doctor --json | python3 -m json.tool >/dev/null
```

Expected:

- All tests pass.
- Ruff passes.
- Build produces wheel and sdist.
- Twine check passes.
- Installed wheel reports the expected version.
- `doctor --json` produces valid JSON.

## Compatibility Rules

- Do not change v0.1.x defaults.
- Do not remove `markdown.template`; keep it as a compatibility alias for `markdown.preset` until a later major release.
- Do not make inactive config examples look active.
- Unknown template fields must fail with a clear error.
- Package naming must stay deterministic.
- `--overwrite` and `--skip-existing` must continue to work.
