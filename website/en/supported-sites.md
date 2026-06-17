---
title: Supported Sites
description: Article sources MagicMD supports or can process through the generic adapter.
---

# Supported Sites

MagicMD is not trying to be a universal crawler. Its goal is to turn common public article pages into clean Markdown packages. Support quality differs by platform.

## Heavily Optimized

| Platform                 | Status           | What MagicMD Handles                                                               |
| ------------------------ | ---------------- | ---------------------------------------------------------------------------------- |
| WeChat Official Accounts | Deeply optimized | Images, video links, empty GIFs, editor assets, source metadata, rich text details |
| Juejin                   | Validated        | Code blocks, heading levels, image downloads, direct outbound links                |
| CSDN                     | Validated        | Code block cleanup, Mermaid/chart fallbacks, header links, noisy widget filtering  |

## Generic Pages

Regular web pages use the generic adapter. It works best on clear article pages and blogs, but it does not get the same platform-specific cleanup as WeChat, Juejin, or CSDN.

## Content That May Need Review

- Articles that require login to show the full content.
- Paid, follower-only, or permission-gated content.
- Complex charts rendered entirely by frontend code.
- Videos with temporary signatures or anti-hotlinking.
- Heavy custom layouts, canvas, SVG animation, or interactive widgets.

## Suggested Workflow

Start with a small batch:

```bash
magicmd batch urls.txt -o output/
```

Then check each article's `extraction-report.json`. If there are warnings, compare `article.md` with the original page.
