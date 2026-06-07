---
name: magicmd
description: Use when the user wants public article URLs from WeChat, Juejin, CSDN, or technical blogs converted into Markdown packages, including batch conversion, local media, metadata, and extraction reports.
---

# MagicMD

This repository keeps the publishable Skill at `skills/magicmd/`.

If this root `SKILL.md` is loaded directly, follow the same workflow: call the published `magicmd` CLI, inspect the output package, and report what was created.

Use this skill for public WeChat Official Account, Juejin, CSDN, and generic article pages. Do not use it to bypass login, paywalls, private pages, CAPTCHA, rate limits, or platform access controls.

## Commands

Prefer an installed CLI:

```bash
magicmd doctor
magicmd "<url>" -o output/
magicmd batch urls.txt -o output/
```

If the CLI is not installed, use:

```bash
uvx --from magicmd magicmd doctor
uvx --from magicmd magicmd "<url>" -o output/
uvx --from magicmd magicmd batch urls.txt -o output/
```

Verify `article.md`, `metadata.json`, `extraction-report.json`, media directories, and batch reports before reporting success.
