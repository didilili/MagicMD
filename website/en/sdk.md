---
title: SDK Integration
description: Call MagicMD directly from Python projects and convert public article URLs into structured Markdown results.
---

# SDK Integration

MagicMD already provides a Python SDK. You do not have to shell out to the `magicmd` command when building a backend, CMS, scheduled job, or Agent runtime. Your Python code can import MagicMD directly and receive structured conversion results.

Use the SDK when:

- A user submits an article URL inside your product.
- A background job converts articles and stores them in a database.
- A CMS, Django app, HaoGit-style system, or custom publishing pipeline needs Markdown, metadata, and local media.
- An Agent workflow needs title, Markdown, source data, warnings, and an extraction report.

If you are manually converting articles, start with [Quick Start](/en/quick-start). If you are integrating MagicMD into another Python project, use this page.

## Install

Install MagicMD in your Python project:

```bash
uv add magicmd
```

Or use pip:

```bash
pip install magicmd
```

## Minimal Call

Return the conversion result in memory without forcing a package write:

```python
from magicmd import convert_article

result = convert_article(
    url="https://mp.weixin.qq.com/s/example",
    output_dir=None,
)

print(result.title)
print(result.markdown)
print(result.metadata)
```

`output_dir=None` is useful for previews, deduplication, review queues, or direct database writes. In this mode, images are not downloaded locally.

## Write a Package

If your system needs local images, reports, or a human-reviewable package, pass `output_dir`:

```python
from magicmd import convert_article

result = convert_article(
    url="https://juejin.cn/post/example",
    output_dir="output/import-workdir",
    download_images=True,
)

print(result.package_dir)
print(result.images)
print(result.report)
```

This writes the same package shape as the CLI: `article.md`, `metadata.json`, `extraction-report.json`, and media folders.

## Result Fields

`convert_article()` returns `ArticleConversionResult`. Common fields:

| Field | Meaning |
| --- | --- |
| `title` | Article title. |
| `author` | Author, account, or platform name. |
| `platform` | Platform key such as `wechat`, `juejin`, `csdn`, or `generic`. |
| `source_url` / `canonical_url` | Original and canonical URLs. |
| `published_at` | Publish time when MagicMD can extract it. |
| `markdown` | Converted Markdown body. |
| `content_hash` | Content hash for deduplication. |
| `images` | Image asset list. |
| `warnings` | Fetch, parse, or media warnings. |
| `metadata` | Structured data aligned with `metadata.json`. |
| `report` | Extraction report aligned with `extraction-report.json`. |
| `package_dir` | Package directory when written; empty in memory mode. |

Two image fields are easy to confuse:

| Field | Meaning |
| --- | --- |
| `markdown_path` | The image path currently referenced in Markdown. |
| `local_path` | The actual downloaded file path on disk. |

External systems usually copy the file at `local_path` into their own media directory, then replace `markdown_path` in the Markdown with the new public URL.

## Error Handling

The SDK raises explicit errors by stage, so your app can map failures to task states:

```python
from magicmd import (
    ConversionError,
    FetchError,
    MediaDownloadError,
    ParseError,
    UnsupportedPlatformError,
    convert_article,
)

try:
    result = convert_article("https://mp.weixin.qq.com/s/example", output_dir="output")
except UnsupportedPlatformError:
    # The URL is not supported, or the platform is disabled by config.
    raise
except FetchError:
    # Fetch failed: network error, 403, browser timeout, and similar cases.
    raise
except ParseError:
    # HTML was fetched, but MagicMD could not parse a valid article.
    raise
except MediaDownloadError:
    # Media download failed.
    raise
except ConversionError:
    # Config, writing, or another conversion-stage failure.
    raise
```

## Integration Tips

- Run conversion in a background job instead of blocking a user request.
- Use `content_hash` for deduplication.
- Store `warnings` and `report` for debugging platform changes.
- Use `output_dir` when you need local images, then copy `images[].local_path`.
- Do not depend on login-only, paid, CAPTCHA-protected, or private pages. MagicMD targets public article URLs.

For more detail, see [Python SDK Integration](https://github.com/didilili/MagicMD/blob/main/docs/integrations/python-sdk.md) and [HaoGit Import Notes](https://github.com/didilili/MagicMD/blob/main/docs/integrations/haogit-import.md).
