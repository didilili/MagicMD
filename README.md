# MagicMD

[![PyPI](https://img.shields.io/pypi/v/magicmd?label=PyPI)](https://pypi.org/project/magicmd/)
[![npm](https://img.shields.io/npm/v/magicmd?label=npm)](https://www.npmjs.com/package/magicmd)
[![CI](https://github.com/didilili/MagicMD/actions/workflows/ci.yml/badge.svg)](https://github.com/didilili/MagicMD/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-magicmd.cn-0f9f6e)](https://magicmd.cn/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

中文 | [English](./README_EN.md)

把散落在网页里的好文章，变成你仓库里的 Markdown。

MagicMD 是一个面向公开文章链接的 Markdown 转换工具。你给它一条 URL，或者一整个 URL 列表，它把文章正文、图片、来源信息和转换报告整理成一个可长期保存的内容包。

```bash
uv tool install magicmd
# 或者
npm install -g magicmd
```

```bash
magicmd "https://mp.weixin.qq.com/s/example"
magicmd batch urls.txt -o output/
```

输出不是一段临时文本，而是一份可以直接进入内容工作流的目录：

```text
output/article-title/
├── article.md
├── metadata.json
├── extraction-report.json
└── images/
    ├── img_001.png
    └── img_002.png
```

MagicMD 可以当 CLI 用，也可以作为 Agent Skill 使用。人负责给链接，工具负责落盘；Agent 负责批量整理时，也走同一套规则。

在线文档和配置生成器：[magicmd.cn](https://magicmd.cn/)

## 适合做什么

- 把微信公众号文章保存为 Markdown。
- 把掘金、CSDN 技术文章沉淀到本地知识库。
- 把公开文章批量整理到 GitHub、Hugo、Docusaurus、HaoGit 或自己的站点。
- 给 Agent 一个稳定的“文章链接转 Markdown”能力，而不是每次重新写提示词。

MagicMD 不是浏览器收藏夹，也不是通用爬虫框架。它的目标更窄：**把公开文章页面尽量干净、可追踪、可复用地转成 Markdown 内容包。**

## 和同类工具有什么不同

很多工具可以把网页或文件转成 Markdown。MagicMD 更关心另一个问题：**中文内容平台里的文章，怎么稳定变成能长期维护的 Markdown。**

| 类型                     | 常见特点                                                 | MagicMD 的差异                                                                                                                   |
| ------------------------ | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| 通用网页转 Markdown 工具 | 更适合标准网页、文档页、英文站点或 LLM 输入清洗。        | MagicMD 针对微信公众号、掘金、CSDN 做平台适配，重点处理中文内容平台常见的富文本、跳转链接、代码控件和编辑器噪声。                |
| 微信文章转换脚本         | 往往能抓正文和图片，但配置、批量、报告和多平台扩展有限。 | MagicMD 不只转微信，还保留 `metadata.json`、`extraction-report.json`、批量报告和可配置 Markdown 输出，方便后续发布或自动化处理。 |
| 爬虫框架                 | 能力强，但通常需要自己写解析逻辑、清洗规则和输出结构。   | MagicMD 直接给文章采集场景一个可用 CLI：链接进去，内容包落盘。                                                                   |
| 手动复制到 Markdown      | 可控，但慢，图片、链接、代码块和来源信息很容易丢。       | MagicMD 自动处理图片本地化、标题层级、代码块、链接、来源信息和失败 warning。                                                     |

MagicMD 的优势不是“抓全网”，而是把中文技术内容归档这件事做细：微信视频会提取链接并尝试下载；掘金外链会尽量还原真实目标地址；CSDN 代码块会清理复制按钮、行号和编辑器控件；批量转换会留下报告，方便你知道哪篇文章需要人工复核。

## 安装

推荐用 `uv` 全局安装：

```bash
uv tool install magicmd
magicmd doctor
```

如果你习惯 `pipx`：

```bash
pipx install magicmd
magicmd doctor
```

参与开发或想使用当前源码时，再使用 editable 安装：

```bash
git clone https://github.com/didilili/MagicMD.git
cd MagicMD
uv sync --extra dev
uv run magicmd doctor
```

还没有安装成全局命令时，把下面命令里的 `magicmd` 换成 `uv run magicmd` 即可。

```bash
uv run magicmd batch urls.txt -o output/
```

### PyPI 和 npm

MagicMD 已发布到 PyPI：

```bash
uv tool install magicmd
pipx install magicmd
```

也可以通过 npm 安装。npm 包是一个轻量入口，底层仍调用 PyPI 版 MagicMD CLI，所以需要本机能使用 `uvx`：

```bash
npm install -g magicmd
npx magicmd --version
```

npm wrapper 位于 [npm/magicmd](./npm/magicmd)。它不会重新实现转换逻辑，只会把命令转发给：

```bash
uvx --from magicmd magicmd
```

### Agent Skill

MagicMD 也可以作为 Agent Skill 安装。Skill 不复制转换逻辑，只规定 Agent 什么时候调用 MagicMD、怎么批量运行、转换后检查哪些文件，以及遇到失败时查看哪些报告。

安装源：

```text
Repository: didilili/MagicMD
Skill path: skills/magicmd
```

使用 Codex 的 skill installer：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo didilili/MagicMD \
  --path skills/magicmd
```

安装后重启 Codex，让 `$magicmd` 生效。

## 快速使用

转换单篇文章：

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

指定输出目录：

```bash
magicmd convert "https://juejin.cn/post/example" -o output/
```

批量转换：

```bash
magicmd batch urls.txt -o output/
```

`urls.txt` 一行一个链接：

```text
https://mp.weixin.qq.com/s/example
https://juejin.cn/post/example
https://blog.csdn.net/user/article/details/123
```

重复跑同一批链接时，跳过已经生成过的内容包：

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

确认要重新生成时，覆盖同名输出包：

```bash
magicmd batch urls.txt -o output/ --overwrite
```

只要正文，不下载图片：

```bash
magicmd convert "https://blog.csdn.net/user/article/details/123" --no-images
```

## Python SDK 使用方式

除了 CLI，MagicMD 也可以被其他 Python 项目直接 `import`。这适合 Web 后端、内容管理系统、定时任务或 Agent Runtime：你不需要额外启动一个 MagicMD 服务，也不需要从命令行解析输出目录。

只在内存中返回结果：

```python
from magicmd import convert_article

result = convert_article(
    url="https://mp.weixin.qq.com/s/example",
    platform="auto",
    output_dir=None,
    download_images=True,
    config_path=None,
)

print(result.title)
print(result.markdown)
print(result.metadata)
```

同时生成内容包：

```python
from magicmd import convert_article

result = convert_article(
    url="https://juejin.cn/post/example",
    output_dir="output",
)

print(result.package_dir)
print(result.report)
```

`convert_article()` 返回的是稳定的 Pydantic 对象 `ArticleConversionResult`，常用字段包括：

| 字段                                | 说明                                                                                                                                                                                                              |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title` / `author` / `published_at` | 文章标题、作者和发布时间。                                                                                                                                                                                        |
| `platform`                          | `wechat`、`juejin`、`csdn`、`generic` 等平台标识。                                                                                                                                                                |
| `source_url` / `canonical_url`      | 原始链接和规范链接。                                                                                                                                                                                              |
| `excerpt`                           | 页面能提取到的摘要。                                                                                                                                                                                              |
| `markdown`                          | 转换后的 Markdown 字符串。                                                                                                                                                                                        |
| `content_hash`                      | 基于正文内容生成的 hash，方便去重。                                                                                                                                                                               |
| `images`                            | 图片资产列表，包含 `source_url`、`local_path`、`markdown_path`、`alt`。`markdown_path` 是 Markdown 中实际引用的路径；`local_path` 是本地已下载图片的文件系统路径，方便外部系统复制到自己的 media 目录后重写链接。 |
| `warnings`                          | 抓取、解析、媒体下载中的 warning。                                                                                                                                                                                |
| `metadata`                          | 与 `metadata.json` 对齐的结构化数据。                                                                                                                                                                             |
| `report`                            | 与 `extraction-report.json` 对齐的转换报告。                                                                                                                                                                      |
| `package_dir`                       | 只有传入 `output_dir` 并成功写出内容包时才有值。                                                                                                                                                                  |

错误类型也可以被后端明确捕获：

```python
from magicmd import FetchError, ParseError, UnsupportedPlatformError, convert_article

try:
    result = convert_article("https://mp.weixin.qq.com/s/example")
except UnsupportedPlatformError:
    ...
except FetchError:
    ...
except ParseError:
    ...
```

公开错误类型包括 `UnsupportedPlatformError`、`FetchError`、`ParseError`、`MediaDownloadError` 和 `ConversionError`。MagicMD 不包含 HaoGit 专属字段；HaoGit 或其他系统可以自行把 `result.markdown`、`result.metadata`、`result.images` 写入自己的数据表和媒体目录。

更完整的接入说明见 [docs/integrations/python-sdk.md](./docs/integrations/python-sdk.md)。如果你要接入 CMS、Django 或 HaoGit 一类业务系统，可以参考 [docs/integrations/haogit-import.md](./docs/integrations/haogit-import.md) 和 [examples/python](./examples/python)。

## 支持站点

| 站点                          | 状态       | 默认抓取   | 说明                                                                        |
| ----------------------------- | ---------- | ---------- | --------------------------------------------------------------------------- |
| 微信公众号 `mp.weixin.qq.com` | 稳定主目标 | `camoufox` | v0.1 最主要的验证对象，已做多轮真实样本格式修复。                           |
| 掘金 `juejin.cn`              | 实验支持   | `camoufox` | 已验证首页样本和复杂技术文章，重点看图片、代码块、外链和标题层级。          |
| CSDN `blog.csdn.net`          | 实验支持   | `camoufox` | 已人工检查 10 篇复杂样本，重点修过代码块、Mermaid/SVG、目录链接和控件噪声。 |
| 通用网页                      | 尽力支持   | `http`     | 对标准 `article`、`main` 或 Open Graph 元信息页面做基础提取。               |

更多站点说明见 [docs/supported-sites.md](./docs/supported-sites.md)。

## MagicMD 会生成什么

单篇文章会生成一个内容包：

```text
output/
└── article-title/
    ├── article.md              # Markdown 正文
    ├── metadata.json           # 标题、作者、时间、来源、hash 等
    ├── extraction-report.json  # 抓取、解析、媒体和 warning
    └── images/                 # 下载后的本地图片
```

批量转换会额外生成：

```text
output/
├── batch-report.json           # 适合程序读取
└── batch-report.md             # 适合人工检查
```

默认的 `article.md` 类似这样：

```md
---
title: "Example Article"
author: "Example Author"
platform: "wechat"
source_url: "https://mp.weixin.qq.com/s/example"
---

# Example Article

> Source: wechat
> Author: Example Author
> Original: https://mp.weixin.qq.com/s/example

正文内容...
```

## CLI 和 Skill

MagicMD 有两个入口。

第一个是给人用的 CLI：

```bash
magicmd batch urls.txt -o output/
```

第二个是给 Agent 用的 [skills/magicmd/SKILL.md](./skills/magicmd/SKILL.md)。Skill 把“什么时候使用 MagicMD、怎么运行、检查哪些文件、遇到失败看什么报告”写成固定流程。这样 Agent 不需要每次猜命令，也不会把登录页、付费墙、验证码页面当成正常文章处理。

安装 Skill 时使用仓库路径 `didilili/MagicMD`，Skill 路径 `skills/magicmd`。

如果你未来要把 MagicMD 接入 HaoGit，建议让 Agent 先调用 Skill 完成采集和转换，再把 `article.md`、`metadata.json` 和图片交给发布流程。

## 配置

生成配置文件：

```bash
magicmd config init
```

配置文件示例见 [.magicmd.example.toml](./.magicmd.example.toml)。

常用配置：

```toml
[output]
directory = "output"
overwrite = false
save_debug_html = "on_failure"

[markdown]
template = "default"
front_matter = "yaml"
include_source_block = true
heading_offset = 0

[images]
download = true
directory = "images"
filename_pattern = "img_{index:03d}.{ext}"

[fetch]
timeout_seconds = 20
browser_timeout_seconds = 15
browser_attempts = 2

[ui]
language = "zh-CN"
```

常见选项：

| 配置                             | 说明                                                          |
| -------------------------------- | ------------------------------------------------------------- |
| `output.directory`               | 默认输出目录。                                                |
| `output.overwrite`               | 是否覆盖同名内容包。                                          |
| `output.save_debug_html`         | `always`、`on_failure`、`never`，控制是否保存 `debug.html`。  |
| `markdown.front_matter`          | `yaml` 或 `none`。                                            |
| `markdown.template`              | `default` 或 `clean`。                                        |
| `markdown.heading_offset`        | 统一调整 Markdown 标题层级。                                  |
| `images.download`                | 是否下载图片。                                                |
| `fetch.browser_attempts`         | 浏览器模式失败后的总尝试次数。                                |
| `ui.language`                    | CLI 终端语言，默认中文优先；设置为 `en-US` 可切换为英文提示。 |
| `platforms.<name>.browser`       | 使用 `http` 或 `camoufox`。                                   |
| `platforms.<name>.wait_selector` | 浏览器抓取时等待的选择器。                                    |

检查环境：

```bash
magicmd doctor
```

`doctor` 会检查 Python 版本、MagicMD 版本、配置文件解析、输出目录可写性、Camoufox 是否可用，以及各平台默认抓取方式。脚本、CI 或 Agent 可以使用 JSON 输出：

```bash
magicmd doctor --json
```

## 使用前知道

MagicMD 只处理公开文章页面。它不会绕过登录、付费墙、私有内容、验证码或平台访问限制。

如果遇到 403、验证码、登录限制、视频防盗链或动态资源失效，MagicMD 会尽量保留已经能提取的内容，并在报告里记录 warning 或失败原因。

如果某个平台的页面结构变化导致转换效果下降，建议先保留输出目录里的 `extraction-report.json`，再用同一链接复现问题。真实样本记录放在 [docs/wechat-regression-corpus.md](./docs/wechat-regression-corpus.md) 和 [tests/fixtures/site_validation_manifest.json](./tests/fixtures/site_validation_manifest.json)，不放在首页展开。

## 开发文档

- [docs/development.md](./docs/development.md)：项目结构、核心模块、转换流程和验证命令。
- [docs/supported-sites.md](./docs/supported-sites.md)：当前支持站点和注意事项。
- [docs/troubleshooting.md](./docs/troubleshooting.md)：安装、抓取、媒体和转换效果问题排查。
- [docs/wechat-regression-corpus.md](./docs/wechat-regression-corpus.md)：微信公众号真实样本回归说明。
- [docs/planning/v0.5-roadmap.md](./docs/planning/v0.5-roadmap.md)：v0.5 中文优先与 Agent 使用体验规划。
- [docs/releases/post-release-checklist.md](./docs/releases/post-release-checklist.md)：发布后 PyPI、npm、GitHub Release 和 Skill smoke test 清单。
- [docs/MagicMD-v0.1-design.md](./docs/MagicMD-v0.1-design.md)：v0.1 设计说明。
- [ROADMAP.md](./ROADMAP.md)：后续版本计划。GitHub Issues 主要用于真实用户反馈。

## 接下来

v0.4.0 已把 CLI 提示调整为中文优先，并补齐官网中英文文档、配置生成器语言选项和 Agent Skill 使用说明。下一步会继续做真实样本回归、更多站点适配和业务系统接入体验优化。完整计划见 [ROADMAP.md](./ROADMAP.md)。

## License

[MIT](./LICENSE)
