# MagicMD

[![PyPI](https://img.shields.io/pypi/v/magicmd?label=PyPI)](https://pypi.org/project/magicmd/)
[![npm](https://img.shields.io/npm/v/magicmd?label=npm)](https://www.npmjs.com/package/magicmd)
[![CI](https://github.com/didilili/MagicMD/actions/workflows/ci.yml/badge.svg)](https://github.com/didilili/MagicMD/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-magicmd.cn-0f9f6e)](https://magicmd.cn/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

[中文](./README.md) | English

Turn scattered web articles into Markdown you can keep in your own repository.

MagicMD is a Markdown conversion tool for public article URLs. Give it one URL, or a whole URL list, and it writes the article body, images, source metadata, and extraction reports into a durable content package.

```bash
uv tool install magicmd
# or
npm install -g magicmd
```

```bash
magicmd "https://mp.weixin.qq.com/s/example"
magicmd batch urls.txt -o output/
```

The output is not a temporary blob of text. It is a directory ready for a publishing or archiving workflow:

```text
output/article-title/
├── article.md
├── metadata.json
├── extraction-report.json
└── images/
    ├── img_001.png
    └── img_002.png
```

MagicMD works as a CLI and as an Agent Skill. Humans provide links and get files on disk; agents can use the same repeatable workflow for batch collection.

Online docs and config builder: [magicmd.cn](https://magicmd.cn/)

## What It Is For

- Saving WeChat Official Account articles as Markdown.
- Moving Juejin and CSDN technical articles into a local knowledge base.
- Preparing public articles for GitHub, Hugo, Docusaurus, HaoGit, or your own site.
- Giving agents a stable "article URL to Markdown" capability instead of rewriting prompts every time.

MagicMD is not a bookmark manager and not a general-purpose crawler framework. Its goal is narrower: **turn public article pages into clean, traceable, reusable Markdown packages.**

## How It Differs From Similar Tools

Many tools can turn web pages or files into Markdown. MagicMD is focused on a more specific problem: **turning Chinese content-platform articles into Markdown that can be maintained over time.**

| Tool type                      | Common focus                                                                                                    | MagicMD's difference                                                                                                                                                        |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Generic URL-to-Markdown tools  | Great for standard web pages, docs, English sites, or LLM input cleanup.                                        | MagicMD has platform adapters for WeChat, Juejin, and CSDN, with cleanup for rich text, redirect links, code widgets, and editor noise common on Chinese content platforms. |
| WeChat-only conversion scripts | Often extract body text and images, but have limited config, batch reporting, and multi-platform extensibility. | MagicMD keeps `metadata.json`, `extraction-report.json`, batch reports, and configurable Markdown output, so the result can feed publishing or automation workflows.        |
| Crawler frameworks             | Powerful, but usually require custom parsing, cleanup rules, and output conventions.                            | MagicMD gives article-collection workflows a ready CLI: links in, content packages on disk.                                                                                 |
| Manual copy to Markdown        | Precise, but slow; images, links, code blocks, and source metadata are easy to lose.                            | MagicMD handles local images, heading depth, code blocks, links, source metadata, and failure warnings automatically.                                                       |

MagicMD's advantage is not "crawl the whole web." It is doing the Chinese technical-content archiving work carefully: WeChat video links are extracted and local download is attempted; Juejin redirect links are normalized back to direct target URLs where possible; CSDN code blocks are cleaned of copy buttons, line counters, and editor widgets; batch conversion leaves a report so you know which articles need review.

## Installation

Recommended global install with `uv`:

```bash
uv tool install magicmd
magicmd doctor
```

If you prefer `pipx`:

```bash
pipx install magicmd
magicmd doctor
```

Use an editable install only when developing MagicMD or running from the current source tree:

```bash
git clone https://github.com/didilili/MagicMD.git
cd MagicMD
uv sync --extra dev
uv run magicmd doctor
```

If MagicMD is not globally installed yet, replace `magicmd` with `uv run magicmd`:

```bash
uv run magicmd batch urls.txt -o output/
```

### PyPI and npm

MagicMD is available on PyPI:

```bash
uv tool install magicmd
pipx install magicmd
```

MagicMD is also available through npm. The npm package is a thin entrypoint that still runs the PyPI CLI, so `uvx` must be available on your machine:

```bash
npm install -g magicmd
npx magicmd --version
```

The npm wrapper lives in [npm/magicmd](./npm/magicmd). It does not reimplement conversion logic; it forwards commands to:

```bash
uvx --from magicmd magicmd
```

### Agent Skill

MagicMD can also be installed as an Agent Skill. The Skill does not duplicate the converter; it tells the agent when to call MagicMD, how to run batch jobs, what files to verify, and which reports to inspect when extraction fails.

Install source:

```text
Repository: didilili/MagicMD
Skill path: skills/magicmd
```

With Codex's skill installer:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo didilili/MagicMD \
  --path skills/magicmd
```

Restart Codex after installing so `$magicmd` is available.

## Quick Start

Convert one article:

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

Choose an output directory:

```bash
magicmd convert "https://juejin.cn/post/example" -o output/
```

Batch conversion:

```bash
magicmd batch urls.txt -o output/
```

`urls.txt` uses one link per line:

```text
https://mp.weixin.qq.com/s/example
https://juejin.cn/post/example
https://blog.csdn.net/user/article/details/123
```

Skip packages that already exist:

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

Overwrite matching output packages:

```bash
magicmd batch urls.txt -o output/ --overwrite
```

Convert Markdown without downloading images:

```bash
magicmd convert "https://blog.csdn.net/user/article/details/123" --no-images
```

## Python SDK

MagicMD can also be imported directly from Python. This is useful for web backends, CMS pipelines, scheduled jobs, and agent runtimes that want structured data instead of parsing CLI output. No extra MagicMD HTTP service is required.

In-memory conversion:

```python
from magicmd import convert_article

result = convert_article(
    url="https://mp.weixin.qq.com/s/example",
    platform="auto",
    output_dir=None,
    download_images=True,
    config_path=None,
)

print(result.title)
print(result.markdown)
print(result.metadata)
```

Write a package and return the same structured result:

```python
from magicmd import convert_article

result = convert_article(
    url="https://juejin.cn/post/example",
    output_dir="output",
)

print(result.package_dir)
print(result.report)
```

`convert_article()` returns a stable Pydantic model named `ArticleConversionResult`:

| Field                               | Meaning                                                                                                                                                                                                                                                                        |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `title` / `author` / `published_at` | Article title, author, and publish time.                                                                                                                                                                                                                                       |
| `platform`                          | Platform key such as `wechat`, `juejin`, `csdn`, or `generic`.                                                                                                                                                                                                                 |
| `source_url` / `canonical_url`      | Original URL and canonical URL.                                                                                                                                                                                                                                                |
| `excerpt`                           | Extracted page summary when available.                                                                                                                                                                                                                                         |
| `markdown`                          | Converted Markdown string.                                                                                                                                                                                                                                                     |
| `content_hash`                      | Hash of the article body for deduplication.                                                                                                                                                                                                                                    |
| `images`                            | Image assets with `source_url`, `local_path`, `markdown_path`, and `alt`. `markdown_path` is the path currently referenced by Markdown; `local_path` is the downloaded filesystem path so external systems can copy the file into their own media directory and rewrite links. |
| `warnings`                          | Fetch, parse, and media warnings.                                                                                                                                                                                                                                              |
| `metadata`                          | Structured data aligned with `metadata.json`.                                                                                                                                                                                                                                  |
| `report`                            | Extraction report aligned with `extraction-report.json`.                                                                                                                                                                                                                       |
| `package_dir`                       | Set only when `output_dir` is provided and a package is written.                                                                                                                                                                                                               |

Backend code can catch explicit SDK errors:

```python
from magicmd import FetchError, ParseError, UnsupportedPlatformError, convert_article

try:
    result = convert_article("https://mp.weixin.qq.com/s/example")
except UnsupportedPlatformError:
    ...
except FetchError:
    ...
except ParseError:
    ...
```

Public errors include `UnsupportedPlatformError`, `FetchError`, `ParseError`, `MediaDownloadError`, and `ConversionError`. MagicMD does not include app-specific fields; external systems can store `result.markdown`, `result.metadata`, and `result.images` in their own database and media pipeline.

See [docs/integrations/python-sdk.md](./docs/integrations/python-sdk.md) for the full SDK contract. For CMS, Django, or HaoGit-style import pipelines, see [docs/integrations/haogit-import.md](./docs/integrations/haogit-import.md) and [examples/python](./examples/python).

## Supported Sites

| Site                                       | Status                | Default fetcher | Notes                                                                                                      |
| ------------------------------------------ | --------------------- | --------------- | ---------------------------------------------------------------------------------------------------------- |
| WeChat Official Account `mp.weixin.qq.com` | Stable primary target | `camoufox`      | Main v0.1 validation target with multiple rounds of live formatting fixes.                                 |
| Juejin `juejin.cn`                         | Experimental support  | `camoufox`      | Homepage and complex technical samples checked for images, code blocks, external links, and heading depth. |
| CSDN `blog.csdn.net`                       | Experimental support  | `camoufox`      | Ten complex live samples manually reviewed for code blocks, Mermaid/SVG, TOC links, and widget noise.      |
| Generic pages                              | Best effort           | `http`          | Basic extraction for pages with standard `article`, `main`, or Open Graph metadata.                        |

See [docs/supported-sites.md](./docs/supported-sites.md) for more site notes.

## What MagicMD Writes

A single conversion writes one content package:

```text
output/
└── article-title/
    ├── article.md              # Markdown article
    ├── metadata.json           # Title, author, time, source, hash, and more
    ├── extraction-report.json  # Fetch, parse, media, and warning details
    └── images/                 # Downloaded local images
```

Batch conversion also writes:

```text
output/
├── batch-report.json           # Machine-readable report
└── batch-report.md             # Human-readable report
```

The default `article.md` looks like this:

```md
---
title: "Example Article"
author: "Example Author"
platform: "wechat"
source_url: "https://mp.weixin.qq.com/s/example"
---

# Example Article

> Source: wechat
> Author: Example Author
> Original: https://mp.weixin.qq.com/s/example

Article body...
```

## CLI and Skill

MagicMD has two entrypoints.

The first one is the human-facing CLI:

```bash
magicmd batch urls.txt -o output/
```

The second one is [skills/magicmd/SKILL.md](./skills/magicmd/SKILL.md) for agents. The Skill records when to use MagicMD, how to run it, which files to check, and where to look when extraction fails. That way an agent does not need to guess the command, and it should not treat login pages, paywalls, or CAPTCHA pages as normal articles.

Install the Skill from repository `didilili/MagicMD` with Skill path `skills/magicmd`.

If you later connect MagicMD to HaoGit, the recommended path is: let the agent use the Skill to collect and convert articles first, then pass `article.md`, `metadata.json`, and local images into the publishing workflow.

## Configuration

Create a config file:

```bash
magicmd config init
```

See [.magicmd.example.toml](./.magicmd.example.toml) for the full example.

Common configuration:

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

[fetch]
timeout_seconds = 20
browser_timeout_seconds = 15
browser_attempts = 2

[ui]
language = "en-US"
```

Useful options:

| Config                           | Meaning                                                                                             |
| -------------------------------- | --------------------------------------------------------------------------------------------------- |
| `output.directory`               | Default output directory.                                                                           |
| `output.overwrite`               | Whether to overwrite an existing package.                                                           |
| `output.save_debug_html`         | `always`, `on_failure`, or `never`; controls `debug.html` output.                                   |
| `markdown.front_matter`          | `yaml` or `none`.                                                                                   |
| `markdown.template`              | `default` or `clean`.                                                                               |
| `markdown.heading_offset`        | Shifts Markdown heading levels.                                                                     |
| `images.download`                | Whether images are downloaded.                                                                      |
| `fetch.browser_attempts`         | Total browser-mode attempts after failures.                                                         |
| `ui.language`                    | CLI terminal language. MagicMD defaults to Chinese-first `zh-CN`; set `en-US` for English messages. |
| `platforms.<name>.browser`       | Uses `http` or `camoufox`.                                                                          |
| `platforms.<name>.wait_selector` | Selector to wait for during browser fetching.                                                       |

Check the runtime:

```bash
magicmd doctor
```

`doctor` checks the Python version, MagicMD version, config parsing, output writability, Camoufox availability, and each platform's default fetch mode. Scripts, CI jobs, or agents can use JSON output:

```bash
magicmd doctor --json
```

## Before You Use

MagicMD only targets public article pages. It does not bypass login, paywalls, private content, CAPTCHA, or platform access controls.

When a page hits 403, CAPTCHA, login restrictions, video hotlink protection, or expired dynamic resources, MagicMD keeps as much extractable content as possible and records warnings or failure reasons in the reports.

If a platform changes its page structure and conversion quality drops, keep the package's `extraction-report.json` and reproduce the issue with the same URL. Live-sample records live in [docs/wechat-regression-corpus.md](./docs/wechat-regression-corpus.md) and [tests/fixtures/site_validation_manifest.json](./tests/fixtures/site_validation_manifest.json) instead of being expanded on the README homepage.

## Developer Docs

- [docs/development.md](./docs/development.md): project structure, core modules, conversion flow, and verification commands.
- [docs/supported-sites.md](./docs/supported-sites.md): supported sites and notes.
- [docs/troubleshooting.md](./docs/troubleshooting.md): install, fetch, media, and conversion-quality troubleshooting.
- [docs/wechat-regression-corpus.md](./docs/wechat-regression-corpus.md): WeChat live regression notes.
- [docs/MagicMD-v0.1-design.md](./docs/MagicMD-v0.1-design.md): v0.1 design notes.
- [ROADMAP.md](./ROADMAP.md): upcoming version plan. GitHub Issues are mainly for real user feedback.

## Next

v0.3.0 adds the public Python SDK, so MagicMD now works as both a CLI and a directly importable library for web backends, content systems, and automation jobs. Next up: more live regression samples, broader site support, and smoother backend integration. See [ROADMAP.md](./ROADMAP.md).

## License

[MIT](./LICENSE)
