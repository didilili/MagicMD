---
title: Publish to GitHub
description: Convert a public article with MagicMD and publish the Markdown package to a GitHub content repository branch or Pull Request.
---

# Publish to GitHub

MagicMD still starts by converting a public article into a local Markdown package. The GitHub publishing workflow adds one optional step after conversion: commit `article.md`, `metadata.json`, `extraction-report.json`, and media files to your content repository.

Use it for Hugo, Docusaurus, blog repositories, knowledge bases, content archives, or any project that stores Markdown content in GitHub.

```text
public article URL -> Markdown package -> GitHub content branch -> optional Pull Request
```

## When to use it

If you only want a local archive, keep using the normal conversion command:

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

If you want to send the converted package to another GitHub repository, such as `owner/content` under `content/posts`, use the publishing command:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --repo owner/content \
  --target-dir content/posts \
  --dry-run
```

## Step 1: Preview with dry-run

Always start with `--dry-run`. It prints the plan only. It does not create branches, commits, pushes, or Pull Requests, and it does not need `GITHUB_TOKEN`.

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --repo owner/content \
  --target-dir content/posts \
  --dry-run
```

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
| `Platform`          | Detected platform                               | WeChat articles usually show `wechat`; generic web pages may show `generic`.                                 |
| `Package directory` | Local package directory                         | Open it and inspect `article.md` and `extraction-report.json`.                                               |
| `Branch`            | Branch that real publishing will push           | Confirm it will not conflict with a branch you are already using.                                            |
| `Target directory`  | Path inside the target repo                     | This is a fixed directory, such as `content/posts`. It does not support template variables today.            |
| `Commit message`    | Commit message for real publishing              | Configure it or override it with `--commit-message`.                                                         |
| `Create PR`         | Whether MagicMD will create a Pull Request      | This becomes `True` when you pass `--pr`.                                                                    |
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

## Step 2: Use a config file

If you publish to the same content repository repeatedly, put the publishing settings in `.magicmd.toml`:

```toml
[publish.github]
repo = "owner/content"
target_dir = "content/posts"
branch = "magicmd/{slug}"
commit_message = "Add article: {title}"
create_pr = false
overwrite = false
```

Then the command can be shorter:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

CLI options override config values. For example:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --repo owner/another-content \
  --dry-run
```

## Config fields

| Field            | Meaning                                                                                                              |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- |
| `repo`           | Target repository in `owner/name` format.                                                                            |
| `target_dir`     | Fixed directory inside the target repository, such as `content/posts`. It does not support template variables today. |
| `branch`         | Publish branch template. Defaults to `magicmd/{slug}`.                                                               |
| `commit_message` | Commit message template. Defaults to `Add article: {title}`.                                                         |
| `create_pr`      | Whether to create a Pull Request after pushing. Override with `--pr` or `--no-pr`.                                   |
| `overwrite`      | Whether planned target files may be overwritten. Override with `--overwrite` or `--no-overwrite`.                    |

`branch` and `commit_message` support these common template variables:

| Variable       | Meaning                                                         |
| -------------- | --------------------------------------------------------------- |
| `{title}`      | Article title                                                   |
| `{slug}`       | URL-friendly title slug                                         |
| `{date}`       | Article publish date, or `undated` when missing                 |
| `{platform}`   | Platform name, such as `wechat`, `juejin`, `csdn`, or `generic` |
| `{short_hash}` | First 6 characters of the content hash                          |

## Step 3: Publish for real

After dry-run looks right, set `GITHUB_TOKEN` and remove `--dry-run`:

```bash
export GITHUB_TOKEN=ghp_xxx

magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --repo owner/content \
  --target-dir content/posts \
  --branch magicmd/{slug}
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

`GITHUB_TOKEN` is not written to `.magicmd.toml` or stored in the git remote URL. Pass it through the environment only.

## Create a Pull Request

Pass `--pr` to create a Pull Request after pushing:

```bash
export GITHUB_TOKEN=ghp_xxx

magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --repo owner/content \
  --target-dir content/posts \
  --branch magicmd/{slug} \
  --pr
```

On success, MagicMD prints the branch, commit, and Pull Request URL. The PR targets the repository default branch.

## Token permissions

Real publishing needs a token that can access and write to the target repository. Usually it must be able to:

- clone the target repository
- push to the publish branch
- create a Pull Request when `--pr` is enabled

If you use a fine-grained token, authorize only the target repository and grant the smallest permissions needed for content writes and Pull Request creation. Do not write the token into config files, README files, shell history, or the repository.

## Common problems

### Missing repo or target_dir

If you do not pass `--repo` and `[publish.github].repo` is missing:

```text
--repo is required unless [publish.github].repo is set
```

If you do not pass `--target-dir` and `[publish.github].target_dir` is missing:

```text
--target-dir is required unless [publish.github].target_dir is set
```

Add the CLI option or put the value in `.magicmd.toml`.

### Missing GITHUB_TOKEN

Dry-run does not need a token. Real publishing does. If the token is missing:

```text
GITHUB_TOKEN is required for real GitHub publishing. Use --dry-run to preview only.
```

Set it and retry:

```bash
export GITHUB_TOKEN=ghp_xxx
```

### Target directory already has files

By default, `overwrite = false`. Publishing stops when the target directory already has unplanned files or when a planned target file already exists. This avoids accidental overwrites in your content repository.

Only use overwrite when you are sure:

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --repo owner/content \
  --target-dir content/posts \
  --overwrite
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
1. Copy a real public article URL
2. Run magicmd publish github URL --dry-run
3. Check title, directory, branch, and file list
4. Open local article.md and review the body
5. Set GITHUB_TOKEN
6. Remove --dry-run and pass --pr
7. Review and merge the Pull Request on GitHub
```
