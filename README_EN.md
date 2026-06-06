# PageMD

[中文](./README.md) | English

PageMD is a CLI tool that turns public article links into Markdown content packages.

It borrows proven ideas from single-platform article converters, but aims to be more complete: cleaner architecture, stronger configuration, multi-platform adapters, normalized metadata, and room for future publishing to GitHub or ingestion into HaoGit.

## Features

- Convert one article URL into a Markdown package.
- Support WeChat public account articles, Juejin, CSDN, and generic public article pages.
- Support batch URL conversion.
- Support configurable Markdown front matter and output structure.
- Download article images and rewrite Markdown image links to local paths.
- Generate `metadata.json` for future publishing to GitHub, HaoGit, or other sites.
- Generate an extraction report for debugging fetch and parsing issues.
- Include `SKILL.md` so PageMD can be used as an Agent Skill.

## Installation

```bash
uv sync --extra dev
```

## Usage

Convert a single article:

```bash
uv run pagemd "https://mp.weixin.qq.com/s/example"
```

Use the explicit `convert` command:

```bash
uv run pagemd convert "https://juejin.cn/post/example" -o output/
```

Batch conversion:

```bash
uv run pagemd batch urls.txt -o output/
```

Initialize config:

```bash
uv run pagemd config init
```

Check the runtime:

```bash
uv run pagemd doctor
```

## Output Structure

```text
output/
└── undated-article-title/
    ├── article.md
    ├── metadata.json
    ├── extraction-report.json
    └── images/
        ├── img_001.png
        └── img_002.png
```

## Project Structure

```text
pagemd/
├── README.md                 # Chinese documentation
├── README_EN.md              # English documentation
├── SKILL.md                  # Agent Skill instructions
├── .pagemd.example.toml      # Example PageMD config
├── pyproject.toml            # Python package metadata, dependencies, and CLI entry
├── uv.lock                   # Locked dependency versions from uv
├── docs/
│   ├── PageMD-v0.1-design.md
│   └── PageMD-v0.1-implementation-plan.md
├── src/
│   └── pagemd/
│       ├── cli.py            # CLI commands and conversion orchestration
│       ├── config.py         # Config loading and defaults
│       ├── detect.py         # URL-based platform detection
│       ├── models.py         # Article, ImageAsset, and ExtractionInfo models
│       ├── output.py         # Output folder, article.md, and metadata.json writing
│       ├── assets.py         # Image downloading and Markdown image link rewriting
│       ├── diagnostics.py    # debug.html and extraction-report.json writing
│       ├── fetchers/
│       │   ├── http.py       # Plain HTTP fetching
│       │   └── browser.py    # Camoufox browser-rendered fetching
│       ├── platforms/
│       │   ├── base.py       # Shared cleanup, image detection, and HTML-to-Markdown helpers
│       │   ├── wechat.py     # WeChat public account parser
│       │   ├── juejin.py     # Juejin parser
│       │   ├── csdn.py       # CSDN parser
│       │   └── generic.py    # Generic web page parser
│       └── renderers/
│           └── markdown.py   # Final Markdown file template
└── tests/
    ├── fixtures/             # HTML fixtures for supported platforms
    └── test_*.py             # Unit and CLI tests
```

## Core Files

| File | Purpose |
| --- | --- |
| `src/pagemd/cli.py` | Defines `pagemd`, `convert`, `batch`, `config init`, and `doctor`, and controls dynamic progress output. |
| `src/pagemd/config.py` | Reads `.pagemd.toml` and merges user config with defaults. |
| `src/pagemd/detect.py` | Detects `wechat`, `juejin`, `csdn`, or `generic` from a URL. |
| `src/pagemd/fetchers/browser.py` | Uses Camoufox for browser-rendered pages, mainly WeChat public account articles. |
| `src/pagemd/fetchers/http.py` | Uses HTTP for regular pages, currently Juejin, CSDN, and generic pages. |
| `src/pagemd/platforms/wechat.py` | Extracts WeChat title, author, publish time, body, images, and code blocks. |
| `src/pagemd/platforms/base.py` | Provides shared body cleanup, image collection, code block preservation, and HTML-to-Markdown conversion. |
| `src/pagemd/renderers/markdown.py` | Controls the final `article.md` format, including front matter, title, source block, and body placement. |
| `src/pagemd/output.py` | Controls output folder naming, `article.md`, `metadata.json`, and content hash writing. |
| `src/pagemd/assets.py` | Downloads images into local `images/` and rewrites remote Markdown image links to local paths. |
| `src/pagemd/models.py` | Defines the standard article structure used by future GitHub publishing and HaoGit imports. |

## Conversion Flow

```text
URL
  ↓
detect.py detects the platform
  ↓
fetchers/http.py or fetchers/browser.py fetches HTML
  ↓
platforms/<platform>.py parses HTML into Article
  ↓
platforms/base.py cleans content and converts it to Markdown
  ↓
assets.py downloads images and rewrites links
  ↓
renderers/markdown.py renders article.md
  ↓
output.py writes article.md, metadata.json, and extraction-report.json
```

## Configuration

Example config file: [.pagemd.example.toml](./.pagemd.example.toml)

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
```

## Agent Skill

This repository includes [SKILL.md](./SKILL.md). Agents that support skills can use it to call PageMD and convert public article links into Markdown packages.

## Safety

PageMD only targets public article pages. It does not bypass login, paywalls, private content, CAPTCHA, or platform access controls.

## Roadmap

- Improve live WeChat article parsing stability.
- Improve live Juejin and CSDN parsing quality.
- Add a Markdown template system.
- Add GitHub publishing.
- Add HaoGit import support.

## Maintenance Rule

The default README is Chinese and the English version lives in the root-level [README_EN.md](./README_EN.md). Future README changes should update both files together so the two versions stay consistent.
