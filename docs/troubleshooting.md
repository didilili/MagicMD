# 排障指南 / Troubleshooting

中文 | English below

这份文档解决一个问题：MagicMD 没按预期工作时，你先看哪里、跑什么命令、该带什么信息反馈。

MagicMD 只处理公开文章页面。登录、付费墙、验证码、私有内容和平台访问限制不属于支持范围。遇到这些情况时，工具会尽量保留已经拿到的内容，并在报告里记录 warning 或失败原因。

## 先跑 doctor

先确认运行环境：

```bash
magicmd doctor
```

脚本、CI 或 Agent 需要机器可读结果时：

```bash
magicmd doctor --json
```

它会检查：

- Python 和 MagicMD 版本
- 配置文件是否能解析
- 输出目录是否可写
- Camoufox 是否可用
- 微信公众号、掘金、CSDN、通用网页的默认抓取方式

如果你是在源码目录里运行，还没有全局安装：

```bash
uv run magicmd doctor
```

## npm 安装后提示缺 uvx

npm 包只是一个轻量入口，真正运行的是 PyPI 版 MagicMD CLI：

```bash
uvx --from magicmd magicmd
```

所以只安装 Node.js 还不够，本机还需要 `uvx`。

macOS / Linux：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

也可以不走 npm，直接安装 Python CLI：

```bash
uv tool install magicmd
pipx install magicmd
```

## Camoufox 不可用

微信公众号、掘金、CSDN 默认使用浏览器模式抓取。如果 `doctor` 里 Camoufox 不可用，先确认当前环境能启动浏览器依赖。

常见处理方式：

```bash
uv run magicmd doctor
```

如果你是通过 PyPI 安装：

```bash
magicmd doctor
```

如果问题只发生在某个站点，保留输出目录里的 `extraction-report.json`。里面会记录平台、抓取方式、阶段、重试次数和 warning。

## 微信公众号 403、验证码或视频打不开

这通常是平台访问限制，不一定是 MagicMD 代码坏了。

常见情况：

- 原文需要登录或微信内访问
- 页面触发验证码或风控
- 视频链接带防盗链，复制出来后浏览器直接打开会 403
- 动态资源已经过期

MagicMD 会尽量做到：

- 能提取视频链接时保留链接
- 不能提取时保留占位说明
- 图片能下载时写入 `images/`
- 抓取或下载失败时写入 `extraction-report.json`

如果视频链接本身被微信限制，MagicMD 不会绕过防盗链。

## 图片缺失或动图为空

先看输出目录：

```text
output/article-title/
├── article.md
├── extraction-report.json
└── images/
```

检查三件事：

1. `article.md` 里图片路径是否指向 `images/`
2. `images/` 里是否真的有文件
3. `extraction-report.json` 里是否有 media warning

微信公众号里有些小动图只是编辑器装饰或占位素材。MagicMD 会过滤一部分空动图和装饰图，避免 Markdown 里出现无意义图片。

## 掘金链接跳转或外链打不开

掘金有些链接会经过平台跳转页。MagicMD 会尽量还原 `title` 或跳转参数里的真实目标链接，减少打开时进入风险提示页。

如果某个链接仍然打不开，请反馈：

- 原文链接
- `article.md` 中对应链接片段
- 浏览器里原始链接元素截图或说明

## CSDN 代码块、Mermaid 或目录问题

CSDN 页面里常见的问题包括：

- 代码块混入复制按钮、行号或“AI 写代码”控件
- Mermaid / SVG 图在页面里不是标准 Markdown
- 文章目录链接指向页面内锚点，转换后可能失效
- 某些代码块内容由前端脚本重排

MagicMD 已经针对真实样本做过清洗，但 CSDN 页面形态很多。如果某篇文章仍然错位，请按下面的反馈格式给信息。

## 批量转换中断后继续

重复跑一批链接时，建议使用：

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

这样已经生成过的内容包会跳过，只继续处理没完成的链接。

如果你确认要重新生成同名输出包：

```bash
magicmd batch urls.txt -o output/ --overwrite
```

## 某篇文章转换效果不好

开 GitHub Issue 时，尽量带上这些信息：

```markdown
## 原文链接

https://...

## 使用命令

magicmd "https://..." -o output/

## 问题描述

例如：代码块错位 / 图片缺失 / 链接不能跳转 / 视频打不开 / 标题层级不对

## 附件或片段

- 输出目录里的 `extraction-report.json`
- `article.md` 中有问题的片段
- 原文截图和转换后截图
```

不要上传 token、cookie、私有文章内容或账号信息。

---

# Troubleshooting

This document answers one question: when MagicMD does not behave as expected, what should you check first, what command should you run, and what information should you include in a report?

MagicMD only targets public article pages. Login-only pages, paywalls, CAPTCHA, private content, and platform access controls are out of scope. In those cases, MagicMD keeps as much extractable content as possible and records warnings or failure reasons in the reports.

## Run doctor first

Check the runtime:

```bash
magicmd doctor
```

For machine-readable output in scripts, CI, or agents:

```bash
magicmd doctor --json
```

It checks:

- Python and MagicMD versions
- config parsing
- output directory writability
- Camoufox availability
- default fetch mode for WeChat, Juejin, CSDN, and generic pages

If you are running from the source tree:

```bash
uv run magicmd doctor
```

## npm says uvx is missing

The npm package is a thin entrypoint. It runs the PyPI CLI through:

```bash
uvx --from magicmd magicmd
```

That means Node.js alone is not enough. `uvx` must also be available.

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

You can also install the Python CLI directly:

```bash
uv tool install magicmd
pipx install magicmd
```

## Camoufox is unavailable

WeChat, Juejin, and CSDN use browser fetching by default. If `doctor` says Camoufox is unavailable, first confirm your environment can start the browser dependency:

```bash
magicmd doctor
```

If the problem only happens on one site, keep `extraction-report.json`. It records the platform, fetcher, stage, retry count, and warnings.

## WeChat 403, CAPTCHA, or video links fail

These are usually platform restrictions, not necessarily a MagicMD bug.

Common cases:

- the original article requires login or in-WeChat access
- the page triggers CAPTCHA or risk control
- video links are protected and return 403 when opened directly
- dynamic resources have expired

MagicMD tries to:

- keep video links when they can be extracted
- keep placeholders when they cannot
- download images into `images/` when possible
- record fetch and media failures in `extraction-report.json`

MagicMD does not bypass WeChat hotlink protection.

## Images are missing or GIFs are blank

Check the output package:

```text
output/article-title/
├── article.md
├── extraction-report.json
└── images/
```

Look at:

1. whether image paths in `article.md` point to `images/`
2. whether files exist in `images/`
3. whether `extraction-report.json` contains media warnings

Some WeChat GIFs are editor decorations or placeholders. MagicMD filters some empty or decorative assets so the Markdown does not keep meaningless images.

## Juejin links still go through redirects

Some Juejin links pass through a redirect page. MagicMD tries to restore the direct target from the `title` attribute or redirect parameters.

If a link still fails, include:

- original article URL
- the related `article.md` link snippet
- a screenshot or note showing the original link element

## CSDN code blocks, Mermaid, or TOC links look wrong

CSDN pages often include:

- copy buttons, line counters, or AI-code widgets inside code blocks
- Mermaid / SVG diagrams that are not standard Markdown
- in-page TOC anchors that may not survive conversion
- code blocks rearranged by frontend scripts

MagicMD already cleans several real-world samples, but CSDN has many page variants. If an article still converts poorly, use the feedback format below.

## Continue an interrupted batch run

When rerunning the same URL list:

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

Existing packages are skipped, and unfinished links continue.

If you want to regenerate matching packages:

```bash
magicmd batch urls.txt -o output/ --overwrite
```

## Reporting a bad conversion

When opening a GitHub Issue, include:

```markdown
## Original URL

https://...

## Command

magicmd "https://..." -o output/

## What went wrong

For example: code block mismatch / missing image / broken link / failed video / wrong heading depth

## Attachments or snippets

- `extraction-report.json`
- the problematic `article.md` snippet
- original and converted screenshots
```

Do not upload tokens, cookies, private article content, or account information.
