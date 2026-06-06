---
name: magicmd
description: Use when converting public article URLs such as WeChat, Juejin, CSDN, or generic technical blog pages into clean Markdown with metadata and local images.
---

# MagicMD

Use MagicMD when the user wants a public article URL converted into Markdown.

Current support:

- Stable primary target: WeChat Official Account articles.
- Experimental browser-mode targets: Juejin and CSDN.
- Best-effort target: generic public article pages.
- Not currently implemented: RSS feed parsing, login-only pages, paywalls, CAPTCHA, or private content.

## Workflow

1. Run `magicmd "<url>" -o <output_dir>`.
2. Check that `article.md` and `metadata.json` exist.
3. Check `images/` when image downloading is enabled.
4. If extraction fails, inspect `debug.html` or the extraction report.
5. Do not bypass login, paywalls, private pages, CAPTCHA, or platform access controls.

## Common Commands

```bash
magicmd "https://mp.weixin.qq.com/s/example" -o output/
magicmd batch urls.txt -o output/
magicmd config init
```
