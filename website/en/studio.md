---
title: MagicMD Studio
description: Use the local web console to convert articles, preview GitHub publishing, and reuse config.
---

# MagicMD Studio

MagicMD Studio is a local web console. It does not upload article content to a MagicMD server. It opens a local address on your machine and puts conversion, output folders, config files, and GitHub publish previews in one interface.

## Start Studio

After installing MagicMD, run:

```bash
magicmd studio
```

Your browser opens the local console:

```text
http://127.0.0.1:8765
```

To avoid opening the browser automatically:

```bash
magicmd studio --no-open
```

If port 8765 is already in use, choose another port:

```bash
magicmd studio --port 8877
```

## First run

1. Paste a public article URL into “Article URL”.
2. Keep the output directory as `output`.
3. Keep the config path as `.magicmd.toml`; conversion can run without a config file.
4. Click “Convert Markdown”.
5. Review the generated directory and file list on the right.

Studio still calls the MagicMD SDK, so the output matches the CLI.

## Publish preview

If `.magicmd.toml` contains `[publish.github]`, click “Preview publish plan”. Studio shows:

- target GitHub repository
- target directory
- publish branch
- commit message
- files that would be written

Publish preview does not create branches, commits, pushes, or Pull Requests. Use it to inspect the result before a real publish.

## Relationship with the CLI

Studio is not a second conversion engine. It turns common commands into an interface:

```bash
magicmd "https://mp.weixin.qq.com/s/example"
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

If you prefer the terminal, keep using the CLI. If you only want to turn articles into Markdown, Studio is the friendlier entry point.

## FAQ

### Why is the publish button currently “Preview publish plan”?

Real publishing writes to your GitHub repository and depends on tokens, permissions, and branch policy. The first Studio version makes the risky step readable before any remote write happens.

### Does Studio store my GitHub token?

No. Real publishing should still use `.env` or the `GITHUB_TOKEN` environment variable. Do not put tokens in `.magicmd.toml`.

### Can I use Studio without a config file?

Yes for Markdown conversion. GitHub publish preview needs `[publish.github]` in `.magicmd.toml`, or you can enable “Generate GitHub publishing config” in the Studio config panel and save it.
