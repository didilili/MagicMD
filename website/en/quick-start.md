---
title: Quick Start
description: Install MagicMD and convert your first public article into a Markdown package.
---

# Quick Start

MagicMD starts with a URL. Give it a public article link, and it creates a Markdown package under `output/` that you can review, publish, or archive.

## Install

Recommended:

```bash
uv tool install magicmd
magicmd doctor
```

If you use `pipx`:

```bash
pipx install magicmd
magicmd doctor
```

The npm package is a lightweight entrypoint that forwards to the PyPI MagicMD CLI:

```bash
npm install -g magicmd
magicmd doctor
```

## Convert One Article

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

Choose an output directory:

```bash
magicmd convert "https://juejin.cn/post/example" -o output/
```

## Batch Convert

Create `urls.txt`:

```text
https://mp.weixin.qq.com/s/example
https://juejin.cn/post/example
https://blog.csdn.net/user/article/details/123
```

Run:

```bash
magicmd batch urls.txt -o output/
```

Resume a batch run by skipping existing packages:

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

## Output

```text
output/article-title/
├── article.md
├── metadata.json
├── extraction-report.json
└── images/
    ├── img_001.png
    └── img_002.png
```

`article.md` contains the converted article, `metadata.json` contains article metadata, and `extraction-report.json` records warnings and extraction details. Batch runs also write a batch report.

## Use a Config File

Copy the example config:

```bash
cp .magicmd.example.toml .magicmd.toml
magicmd "https://mp.weixin.qq.com/s/example" --config .magicmd.toml
```

Or use the [Config Builder](/en/config-builder) to generate a `.magicmd.toml` for your publishing workflow.
