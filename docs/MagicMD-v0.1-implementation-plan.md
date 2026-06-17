# MagicMD v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build MagicMD as an independent Python CLI that converts public article URLs into configurable Markdown packages with metadata, images, and debug artifacts.

**Architecture:** MagicMD is not a fork-shaped rewrite of `wechat-article-to-markdown`; it is a modular CLI with platform adapters. The WeChat adapter should reuse the reference project's proven ideas: browser rendering, `#js_content` extraction, `data-src` image handling, code block preservation, and image URL rewriting. Core workflows should stay platform-neutral so Juejin, generic HTML, future CSDN, GitHub publishing, and HaoGit integration can be added without rewriting the CLI.

**Tech Stack:** Python 3.11+, Typer, Pydantic, BeautifulSoup, markdownify, httpx, Camoufox, pytest, ruff.

---

## File Structure

Create the repository at:

```text
/Users/tools/Desktop/magicmd
```

Initial files:

```text
magicmd/
├── .gitignore
├── .magicmd.example.toml
├── README.md
├── SKILL.md
├── pyproject.toml
├── docs/
│   ├── MagicMD-v0.1-design.md
│   └── MagicMD-v0.1-implementation-plan.md
├── src/
│   └── magicmd/
│       ├── __init__.py
│       ├── assets.py
│       ├── cli.py
│       ├── config.py
│       ├── detect.py
│       ├── diagnostics.py
│       ├── models.py
│       ├── output.py
│       ├── fetchers/
│       │   ├── __init__.py
│       │   ├── browser.py
│       │   └── http.py
│       ├── platforms/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── generic.py
│       │   ├── juejin.py
│       │   └── wechat.py
│       └── renderers/
│           ├── __init__.py
│           └── markdown.py
└── tests/
    ├── fixtures/
    │   ├── generic/basic.html
    │   ├── juejin/basic.html
    │   └── wechat/basic.html
    ├── test_assets.py
    ├── test_cli.py
    ├── test_config.py
    ├── test_detect.py
    ├── test_markdown.py
    ├── test_output.py
    └── test_platforms.py
```

## Task 1: Scaffold Repository and Package

**Files:**

- Create: `/Users/tools/Desktop/magicmd/pyproject.toml`
- Create: `/Users/tools/Desktop/magicmd/.gitignore`
- Create: `/Users/tools/Desktop/magicmd/src/magicmd/__init__.py`
- Create package directories listed above.

- [ ] Create the repository directory and initialize git.

Run:

```bash
mkdir -p /Users/tools/Desktop/magicmd
cd /Users/tools/Desktop/magicmd
git init
```

Expected: a new git repository exists at `/Users/tools/Desktop/magicmd`.

- [ ] Create `pyproject.toml`.

Use:

```toml
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "magicmd"
version = "0.1.0"
description = "Convert public article links into configurable Markdown packages."
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [{ name = "MagicMD Contributors" }]
dependencies = [
  "beautifulsoup4>=4.12",
  "camoufox[geoip]>=0.4",
  "httpx>=0.27",
  "markdownify>=0.13",
  "pydantic>=2.8",
  "typer>=0.12"
]
keywords = ["markdown", "article", "wechat", "juejin", "crawler"]

[project.scripts]
magicmd = "magicmd.cli:app"

[project.optional-dependencies]
dev = ["pytest>=8.2", "pytest-asyncio>=0.23", "ruff>=0.6"]

[tool.hatch.build.targets.wheel]
packages = ["src/magicmd"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["e2e: live tests that require network and browser runtime"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] Create `.gitignore`.

Use:

```gitignore
.DS_Store
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
dist/
build/
*.egg-info/
output/
debug.html
.magicmd.toml
```

- [ ] Create package directories and `__init__.py` files.

Run:

```bash
mkdir -p src/magicmd/{fetchers,platforms,renderers} tests/fixtures/{wechat,juejin,generic} docs
touch src/magicmd/__init__.py src/magicmd/fetchers/__init__.py src/magicmd/platforms/__init__.py src/magicmd/renderers/__init__.py
```

- [ ] Install and run an empty test command.

Run:

```bash
uv sync --extra dev
uv run pytest -q
```

Expected: pytest reports no tests collected or all current tests pass.

## Task 2: Data Models

**Files:**

- Create: `/Users/tools/Desktop/magicmd/src/magicmd/models.py`
- Test: `/Users/tools/Desktop/magicmd/tests/test_models.py`

- [ ] Write tests for normalized article and metadata serialization.

Create `tests/test_models.py`:

```python
from magicmd.models import Article, ExtractionInfo, ImageAsset


def test_article_metadata_dump_uses_stable_keys():
    article = Article(
        title="Codex 实战",
        author="HaoGit",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        canonical_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-06T12:00:00+08:00",
        excerpt="摘要",
        content_markdown="正文",
        content_html="<p>正文</p>",
        images=[
            ImageAsset(
                source_url="https://example.com/a.png",
                local_path="images/img_001.png",
                alt="diagram",
            )
        ],
        extraction=ExtractionInfo(status="success", platform="wechat", parser="wechat"),
    )

    data = article.to_metadata()

    assert data["title"] == "Codex 实战"
    assert data["platform"] == "wechat"
    assert data["images"][0]["local_path"] == "images/img_001.png"
    assert data["extraction"]["status"] == "success"
    assert "content_markdown" not in data
    assert "content_html" not in data
```

- [ ] Run test to verify failure.

Run:

```bash
uv run pytest tests/test_models.py -q
```

Expected: FAIL because `magicmd.models` does not exist yet.

- [ ] Implement `models.py`.

Use:

```python
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
```

- [ ] Run test to verify pass.

Run:

```bash
uv run pytest tests/test_models.py -q
```

Expected: PASS.

## Task 3: Platform Detection and Config

**Files:**

- Create: `/Users/tools/Desktop/magicmd/src/magicmd/detect.py`
- Create: `/Users/tools/Desktop/magicmd/src/magicmd/config.py`
- Create: `/Users/tools/Desktop/magicmd/.magicmd.example.toml`
- Test: `/Users/tools/Desktop/magicmd/tests/test_detect.py`
- Test: `/Users/tools/Desktop/magicmd/tests/test_config.py`

- [ ] Add detection tests.

Create `tests/test_detect.py`:

```python
import pytest

from magicmd.detect import detect_platform


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://mp.weixin.qq.com/s/abc", "wechat"),
        ("https://juejin.cn/post/123", "juejin"),
        ("https://blog.example.com/a", "generic"),
    ],
)
def test_detect_platform(url, expected):
    assert detect_platform(url) == expected
```

- [ ] Add config tests.

Create `tests/test_config.py`:

```python
from pathlib import Path

from magicmd.config import load_config


def test_load_config_merges_toml_file(tmp_path: Path):
    config_path = tmp_path / ".magicmd.toml"
    config_path.write_text(
        """
        [output]
        directory = "articles"

        [images]
        download = false
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output.directory == "articles"
    assert config.images.download is False
    assert config.images.directory == "images"
```

- [ ] Implement `detect.py`.

Use:

```python
from urllib.parse import urlparse


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "mp.weixin.qq.com" in host:
        return "wechat"
    if "juejin.cn" in host:
        return "juejin"
    return "generic"
```

- [ ] Implement `config.py`.

Use:

```python
from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel


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
    user_agent: str = "default"


class PlatformConfig(BaseModel):
    enabled: bool = True
    browser: str = "http"
    wait_selector: str = ""


class MagicMDConfig(BaseModel):
    output: OutputConfig = OutputConfig()
    markdown: MarkdownConfig = MarkdownConfig()
    images: ImagesConfig = ImagesConfig()
    fetch: FetchConfig = FetchConfig()
    platforms: dict[str, PlatformConfig] = {
        "wechat": PlatformConfig(browser="camoufox", wait_selector="#js_content"),
        "juejin": PlatformConfig(browser="http"),
        "generic": PlatformConfig(browser="http"),
    }


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
```

- [ ] Run focused tests.

Run:

```bash
uv run pytest tests/test_detect.py tests/test_config.py -q
```

Expected: PASS.

## Task 4: Markdown Renderer and Output Writer

**Files:**

- Create: `/Users/tools/Desktop/magicmd/src/magicmd/renderers/markdown.py`
- Create: `/Users/tools/Desktop/magicmd/src/magicmd/output.py`
- Test: `/Users/tools/Desktop/magicmd/tests/test_markdown.py`
- Test: `/Users/tools/Desktop/magicmd/tests/test_output.py`

- [ ] Test Markdown rendering.

Create `tests/test_markdown.py`:

```python
from magicmd.models import Article, ExtractionInfo
from magicmd.renderers.markdown import render_markdown


def test_render_markdown_includes_front_matter_and_source_block():
    article = Article(
        title="Codex 实战",
        author="HaoGit",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-06T12:00:00+08:00",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    md = render_markdown(article)

    assert 'title: "Codex 实战"' in md
    assert 'platform: "wechat"' in md
    assert "# Codex 实战" in md
    assert "> Original: https://mp.weixin.qq.com/s/demo" in md
    assert md.rstrip().endswith("正文")
```

- [ ] Test output package writing.

Create `tests/test_output.py`:

```python
import json
from pathlib import Path

from magicmd.models import Article, ExtractionInfo
from magicmd.output import write_article_package


def test_write_article_package_creates_markdown_and_metadata(tmp_path: Path):
    article = Article(
        title="Codex 实战",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    package_dir = write_article_package(article, tmp_path)

    assert (package_dir / "article.md").exists()
    metadata = json.loads((package_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["title"] == "Codex 实战"
```

- [ ] Implement renderer.

Use:

```python
from __future__ import annotations

from magicmd.models import Article


def _quote(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def render_markdown(article: Article) -> str:
    lines = [
        "---",
        f"title: {_quote(article.title)}",
        f"author: {_quote(article.author)}",
        f"platform: {_quote(article.platform)}",
        f"source_url: {_quote(article.source_url)}",
        f"published_at: {_quote(article.published_at)}",
        "---",
        "",
        f"# {article.title}",
        "",
    ]
    lines.extend(
        [
            f"> Source: {article.platform}",
            f"> Author: {article.author}" if article.author else "> Author:",
            f"> Original: {article.source_url}",
            "",
            "---",
            "",
            article.content_markdown.strip(),
            "",
        ]
    )
    return "\n".join(lines)
```

- [ ] Implement output writer.

Use:

```python
from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path

from magicmd.models import Article
from magicmd.renderers.markdown import render_markdown


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title.lower(), flags=re.UNICODE).strip("-")
    return slug[:80] or "article"


def ensure_content_hash(article: Article) -> Article:
    if article.content_hash:
        return article
    digest = sha256(article.content_markdown.encode("utf-8")).hexdigest()
    return article.model_copy(update={"content_hash": digest})


def write_article_package(article: Article, output_dir: str | Path, overwrite: bool = False) -> Path:
    article = ensure_content_hash(article)
    base = Path(output_dir)
    slug = slugify_title(article.title)
    prefix = article.published_at[:10] if article.published_at else "undated"
    package_dir = base / f"{prefix}-{slug}"
    if package_dir.exists() and not overwrite:
        package_dir = base / f"{prefix}-{slug}-{article.content_hash[:6]}"
    package_dir.mkdir(parents=True, exist_ok=overwrite)
    (package_dir / "article.md").write_text(render_markdown(article), encoding="utf-8")
    (package_dir / "metadata.json").write_text(
        json.dumps(article.to_metadata(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return package_dir
```

- [ ] Run focused tests.

Run:

```bash
uv run pytest tests/test_markdown.py tests/test_output.py -q
```

Expected: PASS.

## Task 5: Platform Parsers

**Files:**

- Create: `/Users/tools/Desktop/magicmd/src/magicmd/platforms/wechat.py`
- Create: `/Users/tools/Desktop/magicmd/src/magicmd/platforms/juejin.py`
- Create: `/Users/tools/Desktop/magicmd/src/magicmd/platforms/generic.py`
- Create: fixture files under `/Users/tools/Desktop/magicmd/tests/fixtures/`
- Test: `/Users/tools/Desktop/magicmd/tests/test_platforms.py`

- [ ] Add fixture-driven parser tests.

Create `tests/test_platforms.py`:

```python
from pathlib import Path

from magicmd.platforms.generic import parse_generic_html
from magicmd.platforms.juejin import parse_juejin_html
from magicmd.platforms.wechat import parse_wechat_html


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_wechat_html_extracts_title_author_body_and_images():
    html = (FIXTURES / "wechat" / "basic.html").read_text(encoding="utf-8")

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/demo")

    assert article.title == "微信文章标题"
    assert article.author == "MagicMD"
    assert article.platform == "wechat"
    assert "第一段正文" in article.content_markdown
    assert article.images[0].source_url == "https://example.com/wechat.png"


def test_parse_juejin_html_extracts_basic_article():
    html = (FIXTURES / "juejin" / "basic.html").read_text(encoding="utf-8")

    article = parse_juejin_html(html, "https://juejin.cn/post/demo")

    assert article.title == "掘金文章标题"
    assert article.author == "Juejin Author"
    assert "掘金正文" in article.content_markdown


def test_parse_generic_html_uses_article_element():
    html = (FIXTURES / "generic" / "basic.html").read_text(encoding="utf-8")

    article = parse_generic_html(html, "https://example.com/a")

    assert article.title == "通用文章标题"
    assert "通用正文" in article.content_markdown
```

- [ ] Add `tests/fixtures/wechat/basic.html`.

Use:

```html
<html>
  <head>
    <meta property="og:description" content="微信摘要" />
    <script>
      var create_time = "1780000000";
    </script>
  </head>
  <body>
    <h1 id="activity-name">微信文章标题</h1>
    <a id="js_name">MagicMD</a>
    <div id="js_content">
      <p>第一段正文</p>
      <img data-src="https://example.com/wechat.png" alt="图示" />
      <div class="code-snippet__fix">
        <pre data-lang="python"></pre>
        <code>print("hello")</code>
      </div>
    </div>
  </body>
</html>
```

- [ ] Add Juejin and generic fixtures with matching title, author, and article content.

- [ ] Implement parsers using BeautifulSoup and markdownify.

Implementation principle:

```python
# Each parser returns Article, not raw dictionaries.
# Each parser should set ExtractionInfo(platform=..., parser=...).
# Each parser should preserve images as ImageAsset objects and leave local_path blank.
```

- [ ] Run parser tests.

Run:

```bash
uv run pytest tests/test_platforms.py -q
```

Expected: PASS.

## Task 6: Fetchers, Image Assets, and CLI

**Files:**

- Create: `/Users/tools/Desktop/magicmd/src/magicmd/fetchers/http.py`
- Create: `/Users/tools/Desktop/magicmd/src/magicmd/fetchers/browser.py`
- Create: `/Users/tools/Desktop/magicmd/src/magicmd/assets.py`
- Create: `/Users/tools/Desktop/magicmd/src/magicmd/diagnostics.py`
- Create: `/Users/tools/Desktop/magicmd/src/magicmd/cli.py`
- Test: `/Users/tools/Desktop/magicmd/tests/test_assets.py`
- Test: `/Users/tools/Desktop/magicmd/tests/test_cli.py`

- [ ] Add tests for image URL rewriting and CLI command success with mocked fetch.

- [ ] Implement `fetch_http(url, timeout_seconds)` with `httpx.get(..., follow_redirects=True)`.

- [ ] Implement `fetch_browser(url, wait_selector)` with Camoufox, modeled after the reference project but isolated behind this function.

- [ ] Implement `download_images(article, package_dir, config)` so failures append extraction warnings and do not fail the whole article.

- [ ] Implement Typer app with `convert`, root URL alias, `batch`, `config init`, and `doctor`.

- [ ] Run focused tests.

Run:

```bash
uv run pytest tests/test_assets.py tests/test_cli.py -q
```

Expected: PASS.

## Task 7: Documentation and Skill

**Files:**

- Create: `/Users/tools/Desktop/magicmd/README.md`
- Create: `/Users/tools/Desktop/magicmd/SKILL.md`
- Copy: `/Users/tools/Desktop/MagicMD-v0.1-design.md` to `/Users/tools/Desktop/magicmd/docs/MagicMD-v0.1-design.md`
- Copy: `/Users/tools/Desktop/MagicMD-v0.1-implementation-plan.md` to `/Users/tools/Desktop/magicmd/docs/MagicMD-v0.1-implementation-plan.md`

- [ ] Create README with installation, examples, output structure, config, and safety boundaries.

- [ ] Create `SKILL.md`.

Use:

````markdown
---
name: magicmd
description: Use when converting public article URLs such as WeChat, Juejin, CSDN, RSS, or technical blog pages into clean Markdown with metadata and local images.
---

# MagicMD

Use MagicMD when the user wants a public article URL converted into Markdown.

## Workflow

1. Run `magicmd "<url>" -o <output_dir>`.
2. Check that `article.md` and `metadata.json` exist.
3. Check `images/` when image downloading is enabled.
4. If extraction fails, inspect `debug.html` or the extraction report.
5. Do not bypass login, paywalls, private pages, CAPTCHA, or platform access controls.

## Common Commands

```bash
magicmd "https://mp.weixin.qq.com/s/example" -o output/
magicmd batch urls.txt -o output/
magicmd config init
```
````

````

- [ ] Run package verification.

Run:

```bash
uv run pytest -q
uv run ruff check .
uv run magicmd doctor
````

Expected: all commands pass.

## Task 8: Live Smoke Test

**Files:**

- No source edits unless the smoke test reveals a real bug.

- [ ] Run one live WeChat conversion using a public URL chosen by the user or a known test URL.

Run:

```bash
uv run magicmd "<public-wechat-url>" -o output --debug
```

Expected:

```text
Created output package: output/<slug>
```

- [ ] Inspect output files.

Run:

```bash
find output -maxdepth 3 -type f | sort
```

Expected: `article.md`, `metadata.json`, and downloaded images or a controlled warning.

- [ ] Record limitations in README if the live platform blocks extraction.

## Self-Review Notes

- Spec coverage: v0.1 CLI, local Markdown package, metadata, images, debug artifacts, config, WeChat, Juejin, generic fallback, batch mode, and Skill packaging are covered.
- Deliberately deferred: GitHub publishing, HaoGit integration, AI extraction, account-level crawling, login-cookie crawling, scheduler.
- Architectural standard: MagicMD should be stronger than the reference project by being modular, testable, configurable, multi-platform, and ready for future publishing.
