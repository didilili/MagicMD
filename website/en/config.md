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
heading_offset = 0
```

`heading_offset = 0` keeps article headings connected to the top-level article title. If the article title is `#`, major sections usually become `##`.

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
