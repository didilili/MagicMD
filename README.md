# PageMD

中文 | [English](./README_EN.md)

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

README 默认中文，英文版本放在根目录 [README_EN.md](./README_EN.md)。之后修改 README 时，中英文两个文件需要一起更新，避免两种语言版本出现功能描述不一致。

