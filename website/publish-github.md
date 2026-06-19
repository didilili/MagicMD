---
title: 发布到 GitHub 内容仓库
description: 使用 MagicMD 将公开文章转换成 Markdown 内容包，并发布到 GitHub 内容仓库分支或 Pull Request。
---

# 发布到 GitHub 内容仓库

MagicMD 的 GitHub 发布工作流不是让你每次手敲一长串参数。更自然的方式是：先把目标仓库、目录、分支和提交信息写进 `.magicmd.toml`，以后日常发布只需要传文章链接。

```text
配置一次内容仓库 -> dry-run 预览 -> 发布到分支 -> 可选创建 Pull Request
```

## 推荐路径：先配置，再发布

第一次使用时，先用 [配置生成器](/config-builder) 生成 `.magicmd.toml`，或者手动把这一段放进项目根目录的 `.magicmd.toml`：

```toml
[publish.github]
repo = "owner/content"
target_dir = "content/posts"
branch = "magicmd/{slug}"
commit_message = "Add article: {title}"
create_pr = false
overwrite = false
```

把 `owner/content` 换成你的真实内容仓库，例如 `didilili/blog-content`。把 `content/posts` 换成目标仓库里真正存放文章的目录。

配置好之后，日常预览只需要：

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

确认 dry-run 输出正常后，真实发布也只需要：

```bash
export GITHUB_TOKEN=ghp_xxx
magicmd publish github "https://mp.weixin.qq.com/s/example" --pr
```

`--pr` 会在 push 发布分支后创建 Pull Request。如果你在配置里已经设置 `create_pr = true`，也可以省略 `--pr`。

## 什么时候使用

如果你只是想在本机保存文章，继续使用普通转换命令：

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

如果你想把转换结果发布到 Hugo、Docusaurus、博客、知识库或内容归档仓库，再使用：

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

它会先生成本地内容包，再把 `article.md`、`metadata.json`、`extraction-report.json` 和媒体资源规划到你的 GitHub 内容仓库。

## 第一步：配置发布目标

推荐从配置生成器开始：

```text
配置生成器 -> 展开高级设置 -> 勾选“生成 GitHub 发布配置”
```

你需要填写：

| 字段             | 怎么填                                                                                |
| ---------------- | ------------------------------------------------------------------------------------- |
| `repo`           | 目标仓库，格式是 `owner/name`。                                                       |
| `target_dir`     | 目标仓库内的固定目录，例如 `content/posts`。当前不支持模板变量。                      |
| `branch`         | 发布分支模板，默认 `magicmd/{slug}`。                                                 |
| `commit_message` | 发布提交信息模板，默认 `Add article: {title}`。                                       |
| `create_pr`      | 是否在 push 后创建 Pull Request。命令行也可以用 `--pr` 或 `--no-pr` 临时覆盖。        |
| `overwrite`      | 是否允许覆盖已存在的计划文件。命令行也可以用 `--overwrite` 或 `--no-overwrite` 覆盖。 |

`branch` 和 `commit_message` 支持这些常用模板变量：

| 变量           | 含义                                               |
| -------------- | -------------------------------------------------- |
| `{title}`      | 文章标题                                           |
| `{slug}`       | 由标题生成的 URL 友好名称                          |
| `{date}`       | 文章发布日期，缺失时为 `undated`                   |
| `{platform}`   | 平台名，例如 `wechat`、`juejin`、`csdn`、`generic` |
| `{short_hash}` | 内容 hash 的前 6 位                                |

## 第二步：dry-run 预览

配置文件准备好之后，先跑 dry-run：

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

如果 `.magicmd.toml` 不在当前目录，可以显式指定：

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --config path/to/.magicmd.toml \
  --dry-run
```

dry-run 只展示计划，不会创建分支、commit、push 或 Pull Request，也不需要 `GITHUB_TOKEN`。

输出类似：

```text
Publish plan
Repository: owner/content
Title: 一篇真实文章标题
Platform: wechat
Source URL: https://mp.weixin.qq.com/s/example
Package directory: output/2026-06-19-article-title
Branch: magicmd/article-title
Target directory: content/posts
Commit message: Add article: 一篇真实文章标题
Create PR: False
Overwrite: False
Files:
- content/posts/article.md (12000 bytes)
- content/posts/extraction-report.json (320 bytes)
- content/posts/metadata.json (820 bytes)
- content/posts/images/img_001.png (43120 bytes)
Dry run only: no remote writes were performed.
```

## 看懂 dry-run 输出

| 字段                | 含义                     | 需要检查什么                                                                       |
| ------------------- | ------------------------ | ---------------------------------------------------------------------------------- |
| `Repository`        | 目标 GitHub 仓库         | 应该是真实仓库，例如 `didilili/blog-content`，不要直接用示例里的 `owner/content`。 |
| `Title`             | MagicMD 提取到的文章标题 | 如果这里还是 URL，通常说明示例链接无效、页面受限，或者正文没有被正常提取。         |
| `Platform`          | 识别到的平台             | 微信文章一般是 `wechat`，普通网页可能是 `generic`。                                |
| `Package directory` | 本地生成的内容包目录     | 可以进去检查 `article.md` 和 `extraction-report.json`。                            |
| `Branch`            | 真实发布时会推送的分支   | 确认它不会和你正在使用的分支冲突。                                                 |
| `Target directory`  | 文件写入目标仓库的位置   | 这是固定目录，例如 `content/posts`。当前不支持模板变量。                           |
| `Commit message`    | 真实发布时的提交信息     | 应该能看懂，并且能对应这篇文章。                                                   |
| `Create PR`         | 是否创建 Pull Request    | 加 `--pr` 或配置 `create_pr = true` 后会变成 `True`。                              |
| `Overwrite`         | 是否覆盖已有目标文件     | 默认 `False`，避免误覆盖内容仓库里的文件。                                         |
| `Files`             | 会写入目标仓库的文件清单 | 正常应该包含 `article.md`、`metadata.json`、`extraction-report.json` 和媒体目录。  |

## 识别异常计划

文档里的 `https://mp.weixin.qq.com/s/example` 只是占位示例，不是一篇真实公开文章。如果你直接复制它，dry-run 可能会出现这些信号：

```text
Title: https://mp.weixin.qq.com/s/example
Package directory: output/undated-...
Commit message: Add article: https://mp.weixin.qq.com/s/example
Files:
- content/posts/debug.html
```

这些信号说明这次转换结果不适合发布：

| 信号                        | 可能原因                                     | 建议                                                                                    |
| --------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------- |
| `Title` 是 URL              | 没提取到真实标题                             | 换成真实公开文章链接，再跑 dry-run。                                                    |
| `undated`                   | 没提取到发布时间                             | 不一定失败，但需要检查 `metadata.json`。                                                |
| `debug.html` 出现在 `Files` | MagicMD 保存了调试页面，通常用于排查提取失败 | 先打开本地内容包，检查 `article.md` 和 `extraction-report.json`，确认正文正常后再发布。 |
| `article.md` 很小           | 正文可能没提取到                             | 先不要真实发布，换链接或查看故障排查。                                                  |

dry-run 的价值就在这里：它让你在写入 GitHub 之前发现问题。

## 第三步：真实发布

确认 dry-run 输出正常后，再设置 `GITHUB_TOKEN` 并去掉 `--dry-run`：

```bash
export GITHUB_TOKEN=ghp_xxx

magicmd publish github "https://mp.weixin.qq.com/s/example"
```

真实发布会执行：

```text
1. 转换文章并生成本地内容包
2. 临时 clone 目标 GitHub 仓库
3. 创建或切换发布分支
4. 复制内容包文件到 target_dir
5. 创建 git commit
6. push 到 GitHub
```

`GITHUB_TOKEN` 不会写入 `.magicmd.toml`，也不会写进 git remote URL。请只通过环境变量传入 token。

## 创建 Pull Request

如果希望 MagicMD 在 push 后自动创建 Pull Request，推荐在命令里加 `--pr`：

```bash
export GITHUB_TOKEN=ghp_xxx

magicmd publish github "https://mp.weixin.qq.com/s/example" --pr
```

成功后终端会输出分支、commit 和 Pull Request 链接。PR 的目标分支是仓库默认分支。

## 临时覆盖配置

大多数情况下，用户应该依赖 `.magicmd.toml`。只有临时换仓库、换目录或换分支时，才建议用命令行参数覆盖配置。

例如临时发布到另一个仓库：

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --repo owner/another-content \
  --dry-run
```

例如临时换分支模板：

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" \
  --branch magicmd/{date}-{slug} \
  --dry-run
```

命令行参数优先级高于 `.magicmd.toml`。

## Token 权限

真实发布需要 token 能够访问并写入目标仓库。通常需要：

- clone 目标仓库
- push 到发布分支
- 如果使用 `--pr`，还需要创建 Pull Request

如果使用 fine-grained token，建议只授权目标仓库，并给内容写入和 Pull Request 创建所需的最小权限。不要把 token 写进配置文件、README、shell 历史记录或仓库。

## 常见问题

### 缺少 repo 或 target_dir

如果 `.magicmd.toml` 里没有 `[publish.github].repo`，也没有传 `--repo`，会看到：

```text
--repo is required unless [publish.github].repo is set
```

如果 `.magicmd.toml` 里没有 `[publish.github].target_dir`，也没有传 `--target-dir`，会看到：

```text
--target-dir is required unless [publish.github].target_dir is set
```

先用配置生成器补齐配置，或者临时传命令行参数。

### 缺少 GITHUB_TOKEN

dry-run 不需要 token。真实发布时如果缺少 token，会看到：

```text
GITHUB_TOKEN is required for real GitHub publishing. Use --dry-run to preview only.
```

设置环境变量后重试：

```bash
export GITHUB_TOKEN=ghp_xxx
```

### 目标目录已有文件

默认 `overwrite = false`。如果目标目录已有 MagicMD 计划外的文件，或者目标文件已经存在，发布会停止，避免覆盖你仓库里的内容。

如果你确认可以覆盖计划文件，再使用：

```bash
magicmd publish github "https://mp.weixin.qq.com/s/example" --overwrite
```

### 发布前应该检查什么

真实发布前建议检查这几项：

- `Title` 是真实文章标题，不是 URL。
- `Package directory` 不是 `undated-...`，或者你已经确认没有发布日期也可以接受。
- `Files` 里没有你不想发布的调试文件。
- 本地 `article.md` 正文完整。
- `extraction-report.json` 没有严重 warning。
- `Repository`、`Branch`、`Target directory` 都是你预期的值。

## 推荐工作流

```text
1. 用配置生成器生成 .magicmd.toml
2. 确认 [publish.github] 指向真实内容仓库
3. 复制真实公开文章链接
4. 运行 magicmd publish github URL --dry-run
5. 检查标题、目录、分支、文件列表
6. 打开本地 article.md 复核正文
7. 设置 GITHUB_TOKEN
8. 运行 magicmd publish github URL --pr
9. 在 GitHub 上 review 并 merge
```
