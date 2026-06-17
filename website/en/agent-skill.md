---
title: Agent Skill
description: Install MagicMD as an Agent Skill so Codex, Claude Code, and similar tools can convert public article links from natural-language requests.
---

# Agent Skill

MagicMD can be installed as an Agent Skill. The Skill does not duplicate the converter; it tells the agent when to call MagicMD, how to run batch jobs, what files to verify, and which reports to inspect when extraction fails.

If you do not want to remember commands, treat MagicMD as an agent capability: describe that you want public articles turned into Markdown packages, and the agent can run the CLI, inspect reports, and tell you which results need manual review.

Use it when you want an agent to:

- Convert WeChat Official Account, Juejin, CSDN, or technical blog links in bulk.
- Produce `article.md`, `metadata.json`, and `extraction-report.json` before publishing.
- Review conversion warnings and identify articles that need manual checks.
- Turn public article URLs in a Codex workspace into archive-ready Markdown packages.

## Copyable Agent Requests

After installing the Skill, you can send these requests to Codex, Claude Code, or another Skill-capable agent tool:

```text
Use MagicMD to convert this public article link into a Markdown package, then tell me which files and warnings were produced.
```

```text
Read urls.txt, batch convert the links into output/articles with MagicMD, skip packages that already exist, and report failures from batch-report.md.
```

```text
Run MagicMD doctor and check whether this workspace can convert WeChat, Juejin, CSDN, and generic article links.
```

```text
Inspect this MagicMD output directory and tell me which articles need manual review before publishing.
```

## Install The Skill

The installable MagicMD Skill lives at `skills/magicmd` in this repository:

```text
Repository: didilili/MagicMD
Skill path: skills/magicmd
```

The easiest path is to ask the agent tool you are using, such as Codex, Claude Code, or another tool that supports Skill installation:

```text
Install the MagicMD Skill from GitHub repo didilili/MagicMD, using Skill path skills/magicmd.
```

If you use Codex, you can also run Codex's skill installer manually:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo didilili/MagicMD \
  --path skills/magicmd
```

After installation, the agent will see a Skill named `magicmd`. You can ask it to process one URL, or give it a URL list for batch conversion.

## Runtime Dependency

The Skill only defines the agent workflow. Conversion still runs through the MagicMD CLI.

If MagicMD is installed in the environment, the agent should use:

```bash
magicmd doctor
magicmd "https://mp.weixin.qq.com/s/example" -o output/
magicmd batch urls.txt -o output/
```

If the CLI is not installed globally, the Skill guides the agent to use the PyPI package:

```bash
uvx --from magicmd magicmd doctor
uvx --from magicmd magicmd "https://mp.weixin.qq.com/s/example" -o output/
uvx --from magicmd magicmd batch urls.txt -o output/
```

## What The Agent Does

The Skill gives the agent a fixed workflow:

1. Run `magicmd doctor` when the environment is unknown.
2. Use `magicmd "<url>" -o <output_dir>` for one article.
3. Use `magicmd batch <urls.txt> -o <output_dir>` for many articles.
4. Use `--skip-existing` when resuming a batch.
5. Verify `article.md`, `metadata.json`, and `extraction-report.json`.
6. For batch jobs, inspect `batch-report.md` and `batch-report.json`.

## What The Agent Should Report

After conversion, the agent should report:

- Output directory path.
- Number of successful and failed conversions.
- Important warnings from `extraction-report.json` or `batch-report.md`.
- Whether images or videos were downloaded locally.
- Any limits encountered, such as 403, login requirements, CAPTCHA, video hotlink protection, or missing dynamic resources.
- Suggested next action: publish, manually review, retry, or preserve failure evidence.

## Boundaries

MagicMD only targets public article pages. The Skill should not be used to bypass login, paywalls, private pages, CAPTCHA, rate limits, or platform access controls.

When a page cannot be accessed publicly, MagicMD keeps as much extractable content as possible and records the failure stage or warning in the conversion report.
