# PageMD

中文 | [English](#english)

PageMD 是一个把公开文章链接一键转换为 Markdown 内容包的 CLI 工具。

它参考了单平台文章转换工具的有效经验，但目标更完整：更好的架构、更强的配置能力、多平台适配、标准化元数据，以及后续发布到 GitHub 或接入 HaoGit 的扩展空间。

## 特性

- 输入一个文章 URL，输出 Markdown 内容包。
- 支持微信公众号、掘金、CSDN 和通用公开文章页面。
- 支持批量 URL 转换。
- 支持可配置的 Markdown front matter 和输出结构。
- 自动下载文章图片，并改写 Markdown 图片链接为本地路径。
- 生成 `metadata.json`，方便后续发布到 GitHub、HaoGit 或其他网站。
- 生成 extraction report，方便排查抓取和解析问题。
- 内置 `SKILL.md`，可以作为 Agent Skill 使用。

## 安装

```bash
uv sync --extra dev
```

## 使用

单篇文章转换：

```bash
uv run pagemd "https://mp.weixin.qq.com/s/example"
```

显式使用 `convert` 命令：

```bash
uv run pagemd convert "https://juejin.cn/post/example" -o output/
```

批量转换：

```bash
uv run pagemd batch urls.txt -o output/
```

初始化配置：

```bash
uv run pagemd config init
```

检查运行环境：

```bash
uv run pagemd doctor
```

## 输出结构

```text
output/
└── undated-article-title/
    ├── article.md
    ├── metadata.json
    ├── extraction-report.json
    └── images/
        ├── img_001.png
        └── img_002.png
```

## 配置

示例配置文件：[.pagemd.example.toml](./.pagemd.example.toml)

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
concurrency = 5
```

## Agent Skill

仓库内置 [SKILL.md](./SKILL.md)。支持 Skill 的 Agent 可以根据这份说明调用 PageMD，把公开文章链接转换为 Markdown 内容包。

## 安全边界

PageMD 只处理公开文章页面。它不会绕过登录、付费墙、私有内容、验证码或平台访问限制。

## 路线图

- 增强微信公众号真实页面解析稳定性。
- 增强掘金、CSDN 真实页面解析质量。
- 增加 Markdown 模板系统。
- 增加 GitHub 发布能力。
- 增加 HaoGit 导入能力。

## 维护规则

README 默认先写中文，并提供英文版本。之后修改 README 时，中英文内容需要一起更新，避免两种语言版本出现功能描述不一致。

---

## English

[中文](#pagemd) | English

PageMD is a CLI tool that turns public article links into Markdown content packages.

It borrows proven ideas from single-platform article converters, but aims to be more complete: cleaner architecture, stronger configuration, multi-platform adapters, normalized metadata, and room for future publishing to GitHub or ingestion into HaoGit.

## Features

- Convert one article URL into a Markdown package.
- Support WeChat public account articles, Juejin, CSDN, and generic public article pages.
- Support batch URL conversion.
- Support configurable Markdown front matter and output structure.
- Download article images and rewrite Markdown image links to local paths.
- Generate `metadata.json` for future publishing to GitHub, HaoGit, or other sites.
- Generate an extraction report for debugging fetch and parsing issues.
- Include `SKILL.md` so PageMD can be used as an Agent Skill.

## Installation

```bash
uv sync --extra dev
```

## Usage

Convert a single article:

```bash
uv run pagemd "https://mp.weixin.qq.com/s/example"
```

Use the explicit `convert` command:

```bash
uv run pagemd convert "https://juejin.cn/post/example" -o output/
```

Batch conversion:

```bash
uv run pagemd batch urls.txt -o output/
```

Initialize config:

```bash
uv run pagemd config init
```

Check the runtime:

```bash
uv run pagemd doctor
```

## Output Structure

```text
output/
└── undated-article-title/
    ├── article.md
    ├── metadata.json
    ├── extraction-report.json
    └── images/
        ├── img_001.png
        └── img_002.png
```

## Configuration

Example config file: [.pagemd.example.toml](./.pagemd.example.toml)

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
concurrency = 5
```

## Agent Skill

This repository includes [SKILL.md](./SKILL.md). Agents that support skills can use it to call PageMD and convert public article links into Markdown packages.

## Safety

PageMD only targets public article pages. It does not bypass login, paywalls, private content, CAPTCHA, or platform access controls.

## Roadmap

- Improve live WeChat article parsing stability.
- Improve live Juejin and CSDN parsing quality.
- Add a Markdown template system.
- Add GitHub publishing.
- Add HaoGit import support.

## Maintenance Rule

The README is Chinese-first by default and includes an English version. Future README changes should update both Chinese and English sections together so the two versions stay consistent.
