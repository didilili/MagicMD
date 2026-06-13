---
title: Quick Start
description: Install MagicMD and convert your first public article into a Markdown package.
---

# Quick Start

Run the shortest path first: install the CLI, quickly convert one public article, then open `output/` and inspect the optimized Markdown package. After that, move on to batch conversion and custom output rules.

## 1. Install MagicMD

Use `uv` for the recommended isolated CLI install:

```bash
uv tool install magicmd
magicmd doctor
```

`magicmd doctor` checks the local environment and common dependencies. Once it passes, the conversion commands below are ready to run.

::: details Other install methods

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

:::

## 2. Convert One Article

Copy a public article URL and pass it to MagicMD. It extracts the body, cleans code blocks, handles media, and keeps source metadata:

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

You can also choose an output directory explicitly:

```bash
magicmd convert "https://juejin.cn/post/example" -o output/
```

## 3. Open The Output

MagicMD creates one package directory per article:

```text
output/article-title/
├── article.md
├── metadata.json
├── extraction-report.json
└── images/
    ├── img_001.png
    └── img_002.png
```

`article.md` contains the cleaned article body, `metadata.json` contains article metadata, and `extraction-report.json` records warnings, media download results, and items worth reviewing.

## 4. Batch Convert

Put article links into `urls.txt` and generate packages in bulk:

```text
https://mp.weixin.qq.com/s/example
https://juejin.cn/post/example
https://blog.csdn.net/user/article/details/123
```

Run the batch:

```bash
magicmd batch urls.txt -o output/
```

Resume a batch run by skipping packages that already exist:

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

## 5. Use A Config File

If you publish to Hugo, Docusaurus, or a custom knowledge base, start with a config file so you can customize folders, filenames, metadata, and media paths:

```bash
cp .magicmd.example.toml .magicmd.toml
magicmd "https://mp.weixin.qq.com/s/example" --config .magicmd.toml
```

You can also use the [Config Builder](/en/config-builder) to choose the publishing target, filenames, and media paths, then save the generated `.magicmd.toml` at your project root.
