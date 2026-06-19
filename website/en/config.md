---
title: Configuration
description: Control output naming, Markdown formatting, images, and video paths with .magicmd.toml.
---

# Configuration

MagicMD can read a `.magicmd.toml` file to control output structure. Start from `.magicmd.example.toml`, or generate one with the [Config Builder](/en/config-builder).

## Common Commands

```bash
magicmd "https://mp.weixin.qq.com/s/example" --config .magicmd.toml
magicmd batch urls.txt -o output/ --config .magicmd.toml
```

## GitHub Publishing

```toml
[publish.github]
repo = "owner/content"
target_dir = "content/posts"
branch = "magicmd/{slug}"
commit_message = "Add article: {title}"
create_pr = false
overwrite = false
```

`repo` is the target GitHub repository, and `target_dir` is the content directory inside that repository. `branch` and `commit_message` support template variables such as `{title}`, `{slug}`, `{date}`, `{platform}`, and `{short_hash}`.

CLI options override config values. For example, `--repo` overrides `[publish.github].repo`. `magicmd publish github --dry-run` does not need a token; real publishing requires `GITHUB_TOKEN`.

See [Publish to GitHub](/en/publish-github) for the full command flow, dry-run output, token permissions, and common errors.

## Terminal Language

```toml
[ui]
language = "en-US"
```

`language` controls CLI progress and result messages. MagicMD defaults to Chinese-first `zh-CN`; set it to `en-US` when you prefer English terminal output. This does not rename Markdown front matter keys or the source block template, so Hugo, Docusaurus, and CMS integrations keep reading standard metadata fields.

## Output Naming

```toml
[output]
directory = "output"

[output.naming]
package = "{date}-{slug}"
markdown = "article.md"
metadata = "metadata.json"
report = "extraction-report.json"
docx = "article.docx"
```

Common choices:

| Target                   | Recommendation            |
| ------------------------ | ------------------------- |
| General Markdown archive | `markdown = "article.md"` |
| Hugo content directory   | `markdown = "index.md"`   |
| Docusaurus docs page     | `markdown = "index.md"`   |

## Markdown Format

```toml
[markdown]
preset = "default"
front_matter = "yaml"
include_title = true
include_source_block = true
include_cover_image = true
heading_offset = 0
```

`heading_offset = 0` keeps article headings connected to the top-level article title. If the article title is `#`, major sections usually become `##`.

When `include_cover_image = true`, MagicMD places the WeChat article card cover below the source block and separates it from the body with a horizontal rule. Set it to `false` when you want body-only Markdown.

## Front Matter

```toml
[markdown.front_matter_fields]
title = "{title}"
author = "{author}"
platform = "{platform}"
source_url = "{source_url}"
published_at = "{published_at}"
```

If you want pure Markdown, set `front_matter = "none"`.

## Image Paths

```toml
[images]
download = true
directory = "images"
filename_pattern = "img_{index:03d}.{ext}"
markdown_path = "{directory}/{filename}"
```

If your website stores media in a shared static directory, use a path like:

```toml
[images]
markdown_path = "/static/articles/{slug}/images/{filename}"
```

## Video Paths

```toml
[videos]
download = true
directory = "videos"
filename_pattern = "video_{index:03d}.{ext}"
markdown_path = "{directory}/{filename}"
```

WeChat videos may be protected by temporary signatures, Referer checks, or anti-hotlinking. MagicMD tries to extract and download them; when that fails, it keeps reviewable information in the Markdown or extraction report.

## Word Export

```toml
[docx]
enabled = false
pandoc_path = "pandoc"
reference_doc = ""
```

When `enabled = true`, MagicMD keeps the Markdown package and also generates `article.docx`. You can also enable it for one run with `--format docx`.

DOCX export requires Pandoc. `pandoc_path` defaults to `pandoc` from PATH. `reference_doc` can point to a Word reference DOCX to control title, paragraph, table, and other document styles.
