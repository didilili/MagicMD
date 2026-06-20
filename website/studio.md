---
title: MagicMD Studio
description: 用本地网页控制台完成文章转换、发布预览和配置复用。
---

# MagicMD Studio

MagicMD Studio 是一个本地网页控制台。它不把文章内容上传到 MagicMD 服务器，而是在你的电脑上打开一个本地地址，把文章转换、输出目录、配置文件和 GitHub 发布预览放进同一个界面。

## 启动 Studio

安装 MagicMD 后运行：

```bash
magicmd studio
```

浏览器会自动打开本地控制台：

```text
http://127.0.0.1:8765
```

如果你不想自动打开浏览器：

```bash
magicmd studio --no-open
```

如果 8765 端口已经被占用，可以换一个端口：

```bash
magicmd studio --port 8877
```

## 第一次使用

1. 把公开文章链接粘贴到“文章链接”。
2. 保持输出目录为 `output`。
3. 保持配置文件为 `.magicmd.toml`，如果暂时没有配置文件也可以先转换。
4. 点击“转换 Markdown”。
5. 在右侧查看生成目录和文件列表。

Studio 背后调用的仍然是 MagicMD SDK，所以生成结果和命令行一致。

## 发布预览

如果你已经在 `.magicmd.toml` 里配置了 `[publish.github]`，可以点击“预览发布计划”。Studio 会展示：

- 目标 GitHub 仓库
- 写入目录
- 发布分支
- commit message
- 将写入的文件列表

发布预览不会创建分支、commit、push 或 Pull Request。它适合在真实发布前检查转换结果是否正常。

## 和命令行的关系

Studio 不是另一套转换逻辑。它只是把常用命令变成界面：

```bash
magicmd "https://mp.weixin.qq.com/s/example"
magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run
```

如果你熟悉命令行，可以继续用 CLI；如果你只是想把文章变成 Markdown，Studio 会更直观。

## 常见问题

### 为什么发布按钮现在是“预览发布计划”？

真实发布会写入你的 GitHub 仓库，需要 token、权限和分支策略。Studio 的第一版先把风险最高的一步前置成可读的计划，避免用户在没看懂输出时直接 push。

### Studio 会保存 GitHub token 吗？

不会。真实发布仍然建议通过 `.env` 或环境变量设置 `GITHUB_TOKEN`，不要把 token 写进 `.magicmd.toml`。

### 没有配置文件能用吗？

可以转换 Markdown。GitHub 发布预览需要先在 `.magicmd.toml` 里配置 `[publish.github]`，也可以在 Studio 的配置面板里勾选“生成 GitHub 发布配置”并保存。
