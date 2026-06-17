---
name: magicmd
description: Use when the user wants public article URLs from WeChat, Juejin, CSDN, or technical blogs converted into Markdown packages, including batch conversion, local media, metadata, and extraction reports.
---

# MagicMD

MagicMD converts public article links into Markdown packages. Use it as a thin tool wrapper: call the published CLI, inspect the output, and report what was created.

## User-Facing Prompts

When users are not sure what to ask, suggest concise prompts like these:

```text
Use MagicMD to convert this public article into a Markdown package, then summarize the output files and warnings.
```

```text
Read urls.txt, batch convert all public article links into output/articles with MagicMD, skip existing packages, and report failures from batch-report.md.
```

```text
Use MagicMD doctor to check whether this workspace can convert WeChat, Juejin, CSDN, and generic article links.
```

```text
Inspect this MagicMD output directory and tell me which articles need manual review before publishing.
```

## When to Use

Use this skill for:

- Single public article URL to Markdown conversion.
- Batch conversion from a URL list.
- WeChat Official Account, Juejin, CSDN, and generic public article pages.
- Agent workflows that need `article.md`, metadata, local images, videos, or extraction reports before publishing elsewhere.

Do not use it to bypass login, paywalls, private pages, CAPTCHA, rate limits, or platform access controls.

## Command Choice

Prefer an installed CLI when available:

```bash
magicmd doctor
magicmd "<url>" -o output/
magicmd batch urls.txt -o output/
```

If `magicmd` is not installed, use the PyPI package through `uvx`:

```bash
uvx --from magicmd magicmd doctor
uvx --from magicmd magicmd "<url>" -o output/
uvx --from magicmd magicmd batch urls.txt -o output/
```

For repeated batch runs:

```bash
magicmd batch urls.txt -o output/ --skip-existing
magicmd batch urls.txt -o output/ --overwrite
```

## Workflow

1. Run `magicmd doctor` when the environment is unknown.
2. Put multiple URLs in a plain text file, one URL per line.
3. Convert with `magicmd "<url>" -o <output_dir>` or `magicmd batch <urls.txt> -o <output_dir>`.
4. Verify each output package contains `article.md`, `metadata.json`, and `extraction-report.json`.
5. Check local media directories such as `images/` or `videos/` when media download is enabled.
6. For batch jobs, inspect `batch-report.md` and `batch-report.json`.
7. If conversion is incomplete, inspect `extraction-report.json`, `debug.html` when present, and the source URL.

## Reporting Back

Tell the user:

- Output directory path.
- Number of successful and failed conversions.
- Important warnings from `extraction-report.json` or `batch-report.md`.
- Whether media was downloaded locally.
- Any limits encountered, such as 403, login requirement, video hotlink protection, or missing dynamic resources.
- Next suggested action: publish, manually review, retry with browser support, or collect failure evidence.

Keep the original URL and output package intact so the user can compare against the source page.
