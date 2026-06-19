---
title: Publish to GitHub
description: Convert a public article with MagicMD and publish the Markdown package to a GitHub content repository branch or Pull Request.
---

# Publish to GitHub

MagicMD's GitHub workflow is not meant to make users type a long command every time. The natural path is to put the repository, target directory, branch, and commit message in `.magicmd.toml`, put your local token in `.env`, then publish daily with only the article URL.

```text
configure the content repo once -> save the local token once -> preview with dry-run -> push a branch -> optionally open a Pull Request
```

## Recommended path: configure first, publish later

For the first setup, use the [Config Builder](/en/config-builder), or put this block in `.magicmd.toml` at your project root:

```toml
[publish.github]
repo = "owner/content"
target_dir = "content/posts"
branch = "magicmd/{slug}"
commit_message = "Add article: {title}"
create_pr = false
overwrite = false
```

Replace `owner/content` with your real content repository, such as `didilili/blog-content`. Replace `content/posts` with the directory where your target repository stores articles.

Then create `.env` in the same project root and save your GitHub token:

```dotenv
GITHUB_TOKEN=ghp_xxx
```

`.env` is a private local file. Do not commit it to git. MagicMD reads it automatically for real publishing; dry-run does not need a token.

After that, previewing a publish is short:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

After dry-run looks right, real publishing is short too:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --pr
```

`--pr` creates a Pull Request after pushing the publish branch. If your config already has `create_pr = true`, you can omit `--pr`.

## When to use it

If you only want a local archive, keep using the normal conversion command:

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

If you want to publish the converted package to a Hugo, Docusaurus, blog, knowledge-base, or content archive repository, use:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

MagicMD first creates a local package, then plans `article.md`, `metadata.json`, `extraction-report.json`, and media files into your GitHub content repository.

## Step 1: Configure the publishing target

The recommended path starts in the Config Builder:

```text
Config Builder -> Show advanced settings -> Generate GitHub publishing config
```

Fill in:

| Field            | How to fill it                                                                                                                     |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `repo`           | Target repository in `owner/name` format. You may temporarily pass a GitHub repository URL; MagicMD normalizes it to `owner/name`. |
| `target_dir`     | Fixed directory inside the target repository, such as `content/posts`. It does not support templates today.                        |
| `branch`         | Publish branch template. Defaults to `magicmd/{slug}`.                                                                             |
| `commit_message` | Commit message template. Defaults to `Add article: {title}`.                                                                       |
| `create_pr`      | Whether to create a Pull Request after pushing. Override with `--pr` or `--no-pr`.                                                 |
| `overwrite`      | Whether planned target files may be overwritten. Override with `--overwrite` or `--no-overwrite`.                                  |

`branch` and `commit_message` support these common template variables:

| Variable       | Meaning                                                         |
| -------------- | --------------------------------------------------------------- |
| `{title}`      | Article title                                                   |
| `{slug}`       | URL-friendly title slug                                         |
| `{date}`       | Article publish date, or `undated` when missing                 |
| `{platform}`   | Platform name, such as `wechat`, `juejin`, `csdn`, or `generic` |
| `{short_hash}` | First 6 characters of the content hash                          |

## Step 2: Preview with dry-run

After the config file is ready, run dry-run:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

If `.magicmd.toml` is not in the current directory, pass it explicitly:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --config path/to/.magicmd.toml \
  --dry-run
```

Dry-run prints the plan only. It does not create branches, commits, pushes, or Pull Requests, and it does not need `GITHUB_TOKEN`.

Example output:

```text
Publish plan
Repository: owner/content
Title: A Real Article Title
Platform: wechat
Source URL: https://mp.weixin.qq.com/s/example
Package directory: output/2026-06-19-article-title
Branch: magicmd/article-title
Target directory: content/posts
Commit message: Add article: A Real Article Title
Create PR: False
Overwrite: False
Files:
- content/posts/article.md (12000 bytes)
- content/posts/extraction-report.json (320 bytes)
- content/posts/metadata.json (820 bytes)
- content/posts/images/img_001.png (43120 bytes)
Dry run only: no remote writes were performed.
```

## Read the dry-run output

| Field               | Meaning                                         | What to check                                                                                                |
| ------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `Repository`        | Target GitHub repository                        | Use a real repository, such as `didilili/blog-content`, not the sample `owner/content`.                      |
| `Title`             | Article title extracted by MagicMD              | If this is still the URL, the sample URL may be invalid, blocked, or not parsed correctly.                   |
| `Platform`          | Detected platform                               | WeChat articles usually show `wechat`; generic pages may show `generic`.                                     |
| `Package directory` | Local package directory                         | Open it and inspect `article.md` and `extraction-report.json`.                                               |
| `Branch`            | Branch that real publishing will push           | Confirm it will not conflict with a branch you already use.                                                  |
| `Target directory`  | Path inside the target repo                     | This is a fixed directory, such as `content/posts`. It does not support templates today.                     |
| `Commit message`    | Commit message for real publishing              | It should be readable and clearly match the article.                                                         |
| `Create PR`         | Whether MagicMD will create a Pull Request      | This becomes `True` when you pass `--pr` or set `create_pr = true`.                                          |
| `Overwrite`         | Whether planned target files may be overwritten | Defaults to `False` to avoid accidental overwrites.                                                          |
| `Files`             | Files that would be written to the target repo  | A healthy package usually includes `article.md`, `metadata.json`, `extraction-report.json`, and media files. |

## Spot a bad publish plan

The docs use `https://mp.weixin.qq.com/s/example` as a placeholder, not as a real article. If you run dry-run with that sample URL, you may see:

```text
Title: https://mp.weixin.qq.com/s/example
Package directory: output/undated-...
Commit message: Add article: https://mp.weixin.qq.com/s/example
Files:
- content/posts/debug.html
```

Those are warning signs:

| Signal                          | Likely cause                                                      | What to do                                                                                      |
| ------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `Title` is the URL              | MagicMD did not extract a real title                              | Use a real public article URL and run dry-run again.                                            |
| `undated`                       | MagicMD did not extract a publish date                            | This is not always fatal, but inspect `metadata.json`.                                          |
| `debug.html` appears in `Files` | MagicMD saved a debug page, often because extraction needs review | Open the local package and inspect `article.md` and `extraction-report.json` before publishing. |
| `article.md` is very small      | The article body may be missing                                   | Do not publish yet. Try another URL or inspect the troubleshooting data.                        |

This is the main value of dry-run: you can catch a bad conversion before it reaches GitHub.

When publishing for real, MagicMD checks these risks again. By default, it stops before pushing if extraction failed, the title still looks like the URL, the article Markdown is missing, or the plan includes `debug.html`.

## Step 3: Publish for real

After dry-run looks right, remove `--dry-run` to publish for real. The recommended path is to put the token in `.env` at the project root:

```dotenv
GITHUB_TOKEN=ghp_xxx
```

Then run:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example"
```

Real publishing does this:

```text
1. Convert the article and create a local package
2. Temporarily clone the target GitHub repository
3. Create or check out the publish branch
4. Copy package files into target_dir
5. Create a git commit
6. Push the branch to GitHub
```

`GITHUB_TOKEN` is not written to `.magicmd.toml` or stored in the git remote URL. MagicMD reads the current environment first; if it is missing, it reads `.env`. If you pass `--config path/to/.magicmd.toml`, MagicMD reads `.env` from that config file's directory.

If you understand the risk and still need to publish the package, pass `--force`. This is mainly for internal debugging or one-off migrations:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --force
```

Avoid `--force` for normal publishing.

## Create a Pull Request

Pass `--pr` when you want MagicMD to create a Pull Request after pushing:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --pr
```

On success, MagicMD prints the branch, commit, and Pull Request URL. The PR targets the repository default branch. If `.magicmd.toml` already has `create_pr = true`, you can omit `--pr`.

For one-off publishing, you can skip `.env` and set the token only for the current terminal session:

```bash
export GITHUB_TOKEN=ghp_xxx
magicmd publish github "https://mp.weixin.qq.com/s/example" --pr
```

## Temporarily override config

Most users should rely on `.magicmd.toml`. Use CLI options only when you temporarily need a different repository, directory, or branch.

For example, publish to another repository for one run:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --repo owner/another-content \
  --dry-run
```

Or use a different branch template for one run:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --branch magicmd/{date}-{slug} \
  --dry-run
```

CLI options override `.magicmd.toml`.

## Token permissions

Real publishing needs a token that can access and write to the target repository. Usually it must be able to:

- clone the target repository
- push to the publish branch
- create a Pull Request when `--pr` is enabled

If you use a fine-grained token, authorize only the target repository and grant the smallest permissions needed for content writes and Pull Request creation. Do not write the token into `.magicmd.toml`, README files, shell history, or the repository. Put it in local `.env` and make sure `.env` is not committed.

## Common problems

### Missing repo or target_dir

If `[publish.github].repo` is missing from `.magicmd.toml` and you do not pass `--repo`:

```text
--repo is required unless [publish.github].repo is set
```

If `[publish.github].target_dir` is missing from `.magicmd.toml` and you do not pass `--target-dir`:

```text
--target-dir is required unless [publish.github].target_dir is set
```

Use the Config Builder to complete the config, or pass the CLI option temporarily.

### Missing GITHUB_TOKEN

Dry-run does not need a token. Real publishing does. If the token is missing:

```text
GITHUB_TOKEN is required for real GitHub publishing. Set it in the environment or project .env. Use --dry-run to preview only.
```

Create `.env` at the project root and retry:

```dotenv
GITHUB_TOKEN=ghp_xxx
```

If you pass `--config path/to/.magicmd.toml`, put `.env` next to that config file.

### Target directory already has files

By default, `overwrite = false`. Publishing stops when the target directory already has unplanned files or when a planned target file already exists. This avoids accidental overwrites in your content repository.

Only use overwrite when you are sure:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --overwrite
```

### What to check before publishing

Before real publishing, check:

- `Title` is a real article title, not the URL.
- `Package directory` is not `undated-...`, or you are fine with a missing publish date.
- `Files` does not include debug files you do not want to publish.
- The local `article.md` contains the expected body.
- `extraction-report.json` has no severe warnings.
- `Repository`, `Branch`, and `Target directory` are exactly what you expect.

## Recommended workflow

```text
1. Generate .magicmd.toml with the Config Builder
2. Confirm [publish.github] points to the real content repository
3. Create .env at the project root and add GITHUB_TOKEN
4. Copy a real public article URL
5. Run magicmd publish github URL --dry-run
6. Check title, directory, branch, and file list
7. Open local article.md and review the body
8. Run magicmd publish github URL --pr
9. Review and merge the Pull Request on GitHub
```
