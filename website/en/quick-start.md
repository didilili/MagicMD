---
title: Quick Start
description: Install MagicMD and convert your first public article into a Markdown package.
---

# Quick Start

Run the shortest path first: install MagicMD, open the local Studio console, paste one public article URL, then inspect the generated Markdown package in the interface. After that, move on to batch conversion, custom output rules, and GitHub publishing.

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

## 2. Open Local Studio

For new users, start with the local web console:

```bash
magicmd studio
```

Your browser opens:

```text
http://127.0.0.1:8765
```

Paste an article URL into Studio, click “Convert Markdown”, and review the generated directory, file list, and warnings on the right. See [MagicMD Studio](/en/studio) for details.

## 3. Convert One Article From The CLI

Copy a public article URL and pass it to MagicMD. It extracts the body, cleans code blocks, handles media, and keeps source metadata:

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

You can also choose an output directory explicitly:

```bash
magicmd convert "https://juejin.cn/post/example" -o output/
```

## 4. Open The Output

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

## 5. Batch Convert

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

## 6. Use A Config File

If you publish to Hugo, Docusaurus, or a custom knowledge base, start with a config file so you can customize folders, filenames, metadata, and media paths:

```bash
cp .magicmd.example.toml .magicmd.toml
magicmd "https://mp.weixin.qq.com/s/example" --config .magicmd.toml
```

You can also use the [Config Builder](/en/config-builder) to choose the publishing target, filenames, and media paths, then save the generated `.magicmd.toml` at your project root.

## 7. Publish to a GitHub content repository

Use this when you want to commit converted packages to a Hugo, Docusaurus, blog, or knowledge-base content repository. Start with the [Config Builder](/en/config-builder), enable “Generate GitHub publishing config”, and save the target repository settings in `.magicmd.toml`. See [Publish to GitHub](/en/publish-github) for the full workflow.

After the config is ready, preview the planned write:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

After checking the repository, branch, target path, and file list, publish it:

```dotenv
GITHUB_TOKEN=ghp_xxx
```

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --pr
```

Real publishing requires `GITHUB_TOKEN`. Put it in `.env` at the project root and MagicMD reads it automatically. Dry-run mode does not need a token and does not create branches, commits, pushes, or Pull Requests. If dry-run shows the URL as the title, uses an `undated` directory, or includes `debug.html`, read the [troubleshooting notes in the publishing guide](/en/publish-github#spot-a-bad-publish-plan) before publishing for real.

## 8. Call MagicMD from Python

If you are integrating MagicMD into a Python backend, CMS, HaoGit-style project, or scheduled job, do not parse CLI output. Use [SDK Integration](/en/sdk) and call `from magicmd import convert_article` to receive structured Markdown, metadata, images, and extraction reports.
