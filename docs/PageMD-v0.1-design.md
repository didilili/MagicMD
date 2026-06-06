# PageMD v0.1 Design

## 1. Positioning

PageMD is an independent CLI tool that converts public article URLs into clean, configurable Markdown packages.

The first goal is not to crawl the whole web. The first goal is:

> Given a public article URL, PageMD creates a local Markdown article package with normalized metadata, downloaded images, and debug artifacts when extraction fails.

PageMD should be useful on its own, and later become the ingestion pre-layer for HaoGit or any other content site.

## 2. v0.1 Scope

### In Scope

- Convert one public article URL into Markdown.
- Batch-convert URLs from a plain text file.
- Support WeChat public account articles as the first-class platform.
- Support Juejin as the second platform.
- Keep a generic HTML fallback for other public article pages.
- Generate `article.md`.
- Generate `metadata.json`.
- Download images into a local `images/` directory.
- Rewrite Markdown image links to local image paths.
- Save `debug.html` when extraction fails or when `--debug` is enabled.
- Support configurable Markdown front matter and body template.
- Provide a `SKILL.md` so AI agents can use PageMD as a skill-backed tool.

### Out of Scope for v0.1

- No automatic account-level crawling.
- No login-cookie based crawling.
- No bypassing paywalls, private pages, CAPTCHA, or platform access controls.
- No GitHub publishing yet.
- No HaoGit API integration yet.
- No AI entity extraction yet.
- No scheduler or daemon.

## 3. Core User Flows

### Single URL

```bash
pagemd "https://mp.weixin.qq.com/s/xxx"
```

Expected output:

```text
output/
└── article-slug/
    ├── article.md
    ├── metadata.json
    └── images/
        ├── img_001.png
        └── img_002.png
```

### Explicit Platform

```bash
pagemd "https://mp.weixin.qq.com/s/xxx" --platform wechat
pagemd "https://juejin.cn/post/xxx" --platform juejin
```

### Batch URLs

```bash
pagemd batch urls.txt -o output/
```

`urls.txt` format:

```text
https://mp.weixin.qq.com/s/xxx
https://juejin.cn/post/xxx
```

Blank lines and lines beginning with `#` are ignored.

### Initialize Config

```bash
pagemd config init
```

Creates:

```text
.pagemd.toml
```

## 4. CLI Design

### Commands

```bash
pagemd <url> [options]
pagemd convert <url> [options]
pagemd batch <file> [options]
pagemd config init [options]
pagemd doctor
```

`pagemd <url>` is an alias for `pagemd convert <url>`.

### Common Options

| Option | Meaning |
| --- | --- |
| `-o, --output <dir>` | Output directory. Default: `./output` |
| `--platform <name>` | Force platform: `auto`, `wechat`, `juejin`, `generic` |
| `--template <name>` | Markdown template name |
| `--config <path>` | Config file path |
| `--no-images` | Do not download images |
| `--debug` | Always save debug HTML and extraction report |
| `--overwrite` | Replace existing output directory |
| `--dry-run` | Fetch and parse, but do not write final article files |

## 5. Output Package

### Directory Naming

Default directory name:

```text
YYYY-MM-DD-title-slug
```

Fallback when publish date is unknown:

```text
undated-title-slug
```

If the slug already exists, PageMD appends a short content hash:

```text
2026-06-06-title-slug-a1b2c3
```

### `metadata.json`

```json
{
  "title": "Article title",
  "author": "Author name",
  "platform": "wechat",
  "source_url": "https://mp.weixin.qq.com/s/xxx",
  "canonical_url": "https://mp.weixin.qq.com/s/xxx",
  "published_at": "2026-06-06T12:00:00+08:00",
  "excerpt": "Short excerpt",
  "language": "zh-CN",
  "content_hash": "sha256...",
  "images": [
    {
      "source_url": "https://...",
      "local_path": "images/img_001.png",
      "alt": ""
    }
  ],
  "extraction": {
    "status": "success",
    "platform": "wechat",
    "parser": "wechat",
    "warnings": []
  }
}
```

### `article.md`

Default Markdown output:

```markdown
---
title: "Article title"
author: "Author name"
platform: "wechat"
source_url: "https://mp.weixin.qq.com/s/xxx"
published_at: "2026-06-06T12:00:00+08:00"
---

# Article title

> Source: WeChat
> Author: Author name
> Original: https://mp.weixin.qq.com/s/xxx

---

Article body...
```

## 6. Config Design

`.pagemd.toml`:

```toml
[output]
directory = "output"
overwrite = false
save_debug_html = "on_failure"

[markdown]
template = "default"
front_matter = "yaml"
include_source_block = true
heading_offset = 0

[images]
download = true
directory = "images"
filename_pattern = "img_{index:03d}.{ext}"
concurrency = 5

[fetch]
timeout_seconds = 20
user_agent = "default"

[platforms.wechat]
enabled = true
browser = "camoufox"
wait_selector = "#js_content"

[platforms.juejin]
enabled = true
browser = "http"
```

## 7. Internal Architecture

```text
pagemd/
├── cli.py
├── config.py
├── models.py
├── detect.py
├── fetchers/
│   ├── base.py
│   ├── http.py
│   └── browser.py
├── platforms/
│   ├── base.py
│   ├── wechat.py
│   ├── juejin.py
│   └── generic.py
├── renderers/
│   └── markdown.py
├── assets.py
├── output.py
└── diagnostics.py
```

### Responsibilities

| Module | Responsibility |
| --- | --- |
| `cli.py` | Parse CLI args and orchestrate workflows |
| `config.py` | Load defaults, config files, and CLI overrides |
| `detect.py` | Infer platform from URL |
| `fetchers/` | Fetch raw HTML through HTTP or browser runtime |
| `platforms/` | Extract normalized article data from each platform |
| `models.py` | Define normalized `Article`, `ImageAsset`, and `ExtractionResult` |
| `renderers/markdown.py` | Render Markdown from normalized article data |
| `assets.py` | Download images and rewrite links |
| `output.py` | Create output package atomically |
| `diagnostics.py` | Save debug HTML and extraction reports |

## 8. Platform Strategy

### WeChat

Use browser rendering by default because WeChat article pages are frequently dynamic and sensitive to plain HTTP fetching.

Extraction priorities:

- Title: `#activity-name`, `og:title`, JavaScript variables.
- Author/account: `#js_name`, JavaScript variables.
- Published time: `create_time` script values.
- Content: `#js_content`.
- Images: `data-src` first, then `src`.
- Code blocks: preserve fenced code when possible.

### Juejin

Use normal HTTP first. If the page content is missing, allow browser fallback later.

Extraction priorities:

- Title from page metadata or article heading.
- Author from structured metadata or page author block.
- Published time from structured metadata when available.
- Content from article container.

### Generic HTML

Use a conservative fallback:

- Prefer Open Graph metadata.
- Prefer `<article>`, then common content containers.
- Strip scripts, styles, nav, footer, comments, and ads when possible.
- If confidence is low, save debug output and mark warnings in `metadata.json`.

## 9. Error Handling

PageMD should fail loudly but leave useful artifacts.

| Case | Behavior |
| --- | --- |
| Invalid URL | Exit non-zero with a clear message |
| Fetch timeout | Save extraction report, exit non-zero |
| CAPTCHA or access block suspected | Save `debug.html`, exit non-zero with warning |
| Title missing but content exists | Continue with URL-based title and warning |
| Images fail to download | Continue, keep remote image links or remove according to config |
| Existing output path | Refuse unless `--overwrite` is set |

## 10. Skill Packaging

The same repository should include a lightweight `SKILL.md`.

The skill should not contain the crawler logic. It should teach the agent how to use the CLI:

- When to use PageMD.
- Which command to run.
- How to inspect output.
- How to report failures.
- How to avoid private or restricted content.

Minimal skill trigger:

```yaml
---
name: pagemd
description: Use when converting public article URLs such as WeChat, Juejin, CSDN, RSS, or technical blog pages into clean Markdown with metadata and local images.
---
```

## 11. Future GitHub Publishing

GitHub publishing should be added after local conversion is stable.

Possible command:

```bash
pagemd publish ./output/article-slug --github
pagemd "https://example.com/article" --publish github
```

Future config:

```toml
[publish.github]
enabled = false
repo = "owner/repo"
branch = "main"
base_path = "content/articles"
commit_message = "Add article: {title}"
token_env = "GITHUB_TOKEN"
```

Publishing flow:

1. Validate `GITHUB_TOKEN`.
2. Create or update files in target repo path.
3. Commit to a configurable branch.
4. Optionally open a pull request.

This must stay separate from v0.1 so the first release remains reliable.

## 12. Test Strategy

### Unit Tests

- URL platform detection.
- Config merging.
- Markdown rendering.
- Image link rewriting.
- Slug generation.
- Metadata JSON serialization.

### Fixture Tests

Use saved HTML fixtures:

```text
tests/fixtures/wechat/basic.html
tests/fixtures/wechat/code-images.html
tests/fixtures/juejin/basic.html
tests/fixtures/generic/article.html
```

Tests should not depend on live websites by default.

### Live Tests

Live tests are optional and explicitly marked:

```bash
PAGEMD_E2E_URLS="https://..." pytest -m e2e
```

## 13. v0.1 Milestones

1. Scaffold Python package, CLI, config loader, and data models.
2. Port and clean WeChat extraction from the reference project.
3. Add Markdown renderer and output package writer.
4. Add image downloader and URL rewriting.
5. Add Juejin parser.
6. Add generic fallback parser.
7. Add batch URL mode.
8. Add `SKILL.md`.
9. Add focused tests and one manual live validation path.

## 14. Success Criteria

PageMD v0.1 is successful when:

- A public WeChat article can be converted into `article.md`, `metadata.json`, and local images.
- A public Juejin article can be converted into the same package shape.
- Markdown output format can be changed through config.
- Batch conversion can process multiple URLs and report per-URL success or failure.
- Failures leave enough debug artifacts for manual diagnosis.
- The repository can be installed as a CLI and also used by an AI agent through `SKILL.md`.
