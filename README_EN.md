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

