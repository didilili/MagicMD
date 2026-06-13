---
title: Troubleshooting
description: Fix common install, extraction, media download, and batch conversion issues.
---

# Troubleshooting

Start with:

```bash
magicmd doctor
```

It checks whether MagicMD, Python, browser-related dependencies, and external commands are available in your environment.

## Command Not Found

If MagicMD is not globally installed yet, run:

```bash
uv run magicmd --version
```

Recommended global install:

```bash
uv tool install magicmd
```

If you installed via npm, make sure `uvx` is available:

```bash
uvx --version
magicmd doctor
```

## WeChat Video Fails or Returns 403

WeChat videos often use signatures, Referer checks, or temporary permissions. MagicMD tries to extract and download them. If the download fails, the extraction report keeps the reason. For 403 or expired links, you usually need to review the original article environment manually.

## Missing Images

Check the article's `images/` directory first, then open `extraction-report.json`. Common causes:

- Anti-hotlinking on the original image.
- Network interruption.
- The image is decorative editor material filtered by MagicMD.
- The source page uses lazy loading or unusual image attributes.

## Code Blocks Look Wrong

Upgrade MagicMD and rerun the conversion:

```bash
uv tool upgrade magicmd
magicmd "ARTICLE_URL" -o output/
```

If the issue remains, keep the source URL, `article.md`, and `extraction-report.json`. Those three files are the fastest way to diagnose a platform rule.

## Interrupted Batch Run

Rerun and skip existing packages:

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

To fully rerun one article, delete that article's output directory and run the command again.
