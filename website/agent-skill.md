---
title: Agent Skill
description: 把 MagicMD 作为 Codex/OpenAI Agent Skill 安装，让 Agent 用固定流程转换公开文章链接。
---

# Agent Skill

MagicMD 可以作为 Agent Skill 安装。Skill 不复制转换逻辑；它告诉 Agent 什么时候调用 MagicMD、怎么批量运行、转换后检查哪些文件，以及遇到失败时查看哪些报告。

这适合这些场景：

- 让 Agent 批量整理微信公众号、掘金、CSDN 或技术博客文章。
- 在发布流程前先生成 `article.md`、`metadata.json` 和 `extraction-report.json`。
- 让 Agent 根据转换报告判断哪些文章需要人工复核。
- 在 Codex 工作区里把公开文章链接沉淀成可归档、可发布的 Markdown 内容包。

## 安装 Skill

MagicMD 的可安装 Skill 位于仓库目录 `skills/magicmd`：

```text
Repository: didilili/MagicMD
Skill path: skills/magicmd
```

最简单的方式是直接告诉你正在使用的 Agent 工具，例如 Codex、Claude Code 或其他支持 Skill 安装的工具：

```text
请从 GitHub 仓库 didilili/MagicMD 安装 MagicMD Skill，Skill 路径是 skills/magicmd。
```

安装后，Agent 会看到名为 `magicmd` 的 Skill。你可以让它处理单条链接，也可以让它读取一个 URL 列表后批量转换。

## 运行依赖

Skill 本身只定义 Agent 工作流，真正转换仍然调用 MagicMD CLI。

如果环境里已经安装了 MagicMD，Agent 会优先使用：

```bash
magicmd doctor
magicmd "https://mp.weixin.qq.com/s/example" -o output/
magicmd batch urls.txt -o output/
```

如果没有全局安装，Skill 会引导 Agent 使用 PyPI 包：

```bash
uvx --from magicmd magicmd doctor
uvx --from magicmd magicmd "https://mp.weixin.qq.com/s/example" -o output/
uvx --from magicmd magicmd batch urls.txt -o output/
```

## 如何让 Agent 使用

安装后，你可以直接描述任务：

```text
请用 MagicMD 把这些公众号文章转换成 Markdown 内容包，并告诉我哪些文章有 warning。
```

或者给 Agent 一个链接文件：

```text
请读取 urls.txt，用 MagicMD 批量转换到 output/articles，并跳过已经存在的内容包。
```

Skill 会让 Agent 按固定流程执行：

1. 环境不明确时先运行 `magicmd doctor`。
2. 单篇文章使用 `magicmd "<url>" -o <output_dir>`。
3. 多篇文章使用 `magicmd batch <urls.txt> -o <output_dir>`。
4. 断点续跑时使用 `--skip-existing`。
5. 转换后检查 `article.md`、`metadata.json`、`extraction-report.json`。
6. 批量任务检查 `batch-report.md` 和 `batch-report.json`。

## 输出检查

Agent 完成转换后，应该向你汇报：

- 输出目录路径。
- 成功和失败的数量。
- `extraction-report.json` 或 `batch-report.md` 里的重要 warning。
- 图片或视频是否已下载到本地。
- 是否遇到 403、登录要求、验证码、视频防盗链或动态资源缺失。
