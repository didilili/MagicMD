---
title: 配置说明
description: 使用 .magicmd.toml 控制输出命名、Markdown 格式、图片和视频路径。
---

# 配置说明

MagicMD 支持通过 `.magicmd.toml` 控制输出结构。你可以从项目根目录的 `.magicmd.example.toml` 开始，也可以使用 [配置生成器](/config-builder) 生成。

## 常用命令

```bash
magicmd "https://mp.weixin.qq.com/s/example" --config .magicmd.toml
magicmd batch urls.txt -o output/ --config .magicmd.toml
```

## 终端语言

```toml
[ui]
language = "zh-CN"
```

`language` 控制 CLI 终端进度和结果提示。MagicMD 默认中文优先；如果你想保留英文输出，可以改成 `en-US`。这个配置不会改动 Markdown 的 front matter 字段名或来源信息块模板，避免影响 Hugo、Docusaurus 或 CMS 读取。

## 输出命名

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

常见选择：

| 目标               | 建议                      |
| ------------------ | ------------------------- |
| 普通 Markdown 归档 | `markdown = "article.md"` |
| Hugo 内容目录      | `markdown = "index.md"`   |
| Docusaurus 文档    | `markdown = "index.md"`   |

## Markdown 格式

```toml
[markdown]
preset = "default"
front_matter = "yaml"
include_title = true
include_source_block = true
heading_offset = 0
```

`heading_offset = 0` 表示正文标题会尽量接在文章一级标题之后。比如文章标题是一级标题，正文中的主要章节会从二级标题开始。

## Front matter

```toml
[markdown.front_matter_fields]
title = "{title}"
author = "{author}"
platform = "{platform}"
source_url = "{source_url}"
published_at = "{published_at}"
```

如果你只想要纯 Markdown，可以把 `front_matter` 设置为 `none`。

## 图片路径

```toml
[images]
download = true
directory = "images"
filename_pattern = "img_{index:03d}.{ext}"
markdown_path = "{directory}/{filename}"
```

如果你的网站把图片统一放到静态目录，可以改成：

```toml
[images]
markdown_path = "/static/articles/{slug}/images/{filename}"
```

## 视频路径

```toml
[videos]
download = true
directory = "videos"
filename_pattern = "video_{index:03d}.{ext}"
markdown_path = "{directory}/{filename}"
```

微信视频可能受防盗链或权限限制。MagicMD 会尽量提取链接和下载，无法下载时会在正文或报告里留下可复核信息。

## Word 导出

```toml
[docx]
enabled = false
pandoc_path = "pandoc"
reference_doc = ""
```

`enabled = true` 时，MagicMD 会保留 Markdown 内容包，并额外生成 `article.docx`。你也可以在单次命令里用 `--format docx` 临时开启。

DOCX 导出依赖 Pandoc。`pandoc_path` 默认使用 PATH 中的 `pandoc`；`reference_doc` 可以指向一个 Word reference docx，用来控制标题、正文、表格等样式。
