# MagicMD

中文 | [English](./README_EN.md)

把散落在网页里的好文章，变成你仓库里的 Markdown。

MagicMD 是一个面向公开文章链接的 Markdown 转换工具。你给它一条 URL，或者一整个 URL 列表，它把文章正文、图片、来源信息和转换报告整理成一个可长期保存的内容包。

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

## 适合做什么

- 把微信公众号文章保存为 Markdown。
- 把掘金、CSDN 技术文章沉淀到本地知识库。
- 把公开文章批量整理到 GitHub、Hugo、Docusaurus、HaoGit 或自己的站点。
- 给 Agent 一个稳定的“文章链接转 Markdown”能力，而不是每次重新写提示词。

MagicMD 不是浏览器收藏夹，也不是通用爬虫框架。它的目标更窄：**把公开文章页面尽量干净、可追踪、可复用地转成 Markdown 内容包。**

## 和同类工具有什么不同

很多工具可以把网页或文件转成 Markdown。MagicMD 更关心另一个问题：**中文内容平台里的文章，怎么稳定变成能长期维护的 Markdown。**

| 类型 | 常见特点 | MagicMD 的差异 |
| --- | --- | --- |
| 通用网页转 Markdown 工具 | 更适合标准网页、文档页、英文站点或 LLM 输入清洗。 | MagicMD 针对微信公众号、掘金、CSDN 做平台适配，重点处理中文内容平台常见的富文本、跳转链接、代码控件和编辑器噪声。 |
| 微信文章转换脚本 | 往往能抓正文和图片，但配置、批量、报告和多平台扩展有限。 | MagicMD 不只转微信，还保留 `metadata.json`、`extraction-report.json`、批量报告和可配置 Markdown 输出，方便后续发布或自动化处理。 |
| 爬虫框架 | 能力强，但通常需要自己写解析逻辑、清洗规则和输出结构。 | MagicMD 直接给文章采集场景一个可用 CLI：链接进去，内容包落盘。 |
| 手动复制到 Markdown | 可控，但慢，图片、链接、代码块和来源信息很容易丢。 | MagicMD 自动处理图片本地化、标题层级、代码块、链接、来源信息和失败 warning。 |

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

MagicMD 目前也不是 npm 包，所以暂时不支持：

```bash
npm install -g magicmd
npx magicmd
```

npm 入口适合后续做成轻量 wrapper：用户通过 npm 安装，底层仍调用 MagicMD CLI。v0.1 先把 Python CLI 稳住，再评估这个入口。

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

## 支持站点

| 站点 | 状态 | 默认抓取 | 说明 |
| --- | --- | --- | --- |
| 微信公众号 `mp.weixin.qq.com` | 稳定主目标 | `camoufox` | v0.1 最主要的验证对象，已做多轮真实样本格式修复。 |
| 掘金 `juejin.cn` | 实验支持 | `camoufox` | 已验证首页样本和复杂技术文章，重点看图片、代码块、外链和标题层级。 |
| CSDN `blog.csdn.net` | 实验支持 | `camoufox` | 已人工检查 10 篇复杂样本，重点修过代码块、Mermaid/SVG、目录链接和控件噪声。 |
| 通用网页 | 尽力支持 | `http` | 对标准 `article`、`main` 或 Open Graph 元信息页面做基础提取。 |

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

第二个是给 Agent 用的 [SKILL.md](./SKILL.md)。Skill 把“什么时候使用 MagicMD、怎么运行、检查哪些文件、遇到失败看什么报告”写成固定流程。这样 Agent 不需要每次猜命令，也不会把登录页、付费墙、验证码页面当成正常文章处理。

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
```

常见选项：

| 配置 | 说明 |
| --- | --- |
| `output.directory` | 默认输出目录。 |
| `output.overwrite` | 是否覆盖同名内容包。 |
| `output.save_debug_html` | `always`、`on_failure`、`never`，控制是否保存 `debug.html`。 |
| `markdown.front_matter` | `yaml` 或 `none`。 |
| `markdown.template` | `default` 或 `clean`。 |
| `markdown.heading_offset` | 统一调整 Markdown 标题层级。 |
| `images.download` | 是否下载图片。 |
| `fetch.browser_attempts` | 浏览器模式失败后的总尝试次数。 |
| `platforms.<name>.browser` | 使用 `http` 或 `camoufox`。 |
| `platforms.<name>.wait_selector` | 浏览器抓取时等待的选择器。 |

检查环境：

```bash
magicmd doctor
```

`doctor` 会检查 Python 版本、MagicMD 版本、配置文件解析、输出目录可写性、Camoufox 是否可用，以及各平台默认抓取方式。

## 使用前知道

MagicMD 只处理公开文章页面。它不会绕过登录、付费墙、私有内容、验证码或平台访问限制。

如果遇到 403、验证码、登录限制、视频防盗链或动态资源失效，MagicMD 会尽量保留已经能提取的内容，并在报告里记录 warning 或失败原因。

如果某个平台的页面结构变化导致转换效果下降，建议先保留输出目录里的 `extraction-report.json`，再用同一链接复现问题。真实样本记录放在 [docs/wechat-regression-corpus.md](./docs/wechat-regression-corpus.md) 和 [tests/fixtures/site_validation_manifest.json](./tests/fixtures/site_validation_manifest.json)，不放在首页展开。

## 开发文档

- [docs/development.md](./docs/development.md)：项目结构、核心模块、转换流程和验证命令。
- [docs/supported-sites.md](./docs/supported-sites.md)：当前支持站点和注意事项。
- [docs/wechat-regression-corpus.md](./docs/wechat-regression-corpus.md)：微信公众号真实样本回归说明。
- [docs/MagicMD-v0.1-design.md](./docs/MagicMD-v0.1-design.md)：v0.1 设计说明。

## 接下来

- 评估 npm wrapper，支持 `npm install -g magicmd` 或 `npx magicmd`。
- 完善 PyPI 发布自动化和 project-scoped token 流程。
- 增加 Markdown 模板系统。
- 增加 GitHub 发布能力。
- 增加 HaoGit 导入能力。
- 扩充微信公众号、掘金、CSDN 真实样本回归集。
- 增加更多站点适配器。

## License

[MIT](./LICENSE)
