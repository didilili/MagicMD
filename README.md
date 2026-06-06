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

## 项目目录结构

```text
pagemd/
├── README.md                 # 中文说明文档
├── README_EN.md              # English documentation
├── SKILL.md                  # Agent Skill 使用说明
├── .pagemd.example.toml      # PageMD 配置示例
├── pyproject.toml            # Python 包配置、依赖和 CLI 入口
├── uv.lock                   # uv 锁定依赖版本
├── docs/
│   ├── PageMD-v0.1-design.md
│   └── PageMD-v0.1-implementation-plan.md
├── src/
│   └── pagemd/
│       ├── cli.py            # CLI 命令入口和转换编排
│       ├── config.py         # 配置文件加载与默认配置
│       ├── detect.py         # 根据 URL 判断平台
│       ├── models.py         # Article、ImageAsset、ExtractionInfo 数据模型
│       ├── output.py         # 输出目录、article.md 和 metadata.json 写入
│       ├── assets.py         # 图片下载与 Markdown 图片链接改写
│       ├── diagnostics.py    # debug.html 和 extraction-report.json 写入
│       ├── fetchers/
│       │   ├── http.py       # 普通 HTTP 抓取
│       │   └── browser.py    # Camoufox 浏览器渲染抓取
│       ├── platforms/
│       │   ├── base.py       # 平台通用正文清洗、图片识别、HTML 转 Markdown
│       │   ├── wechat.py     # 微信公众号解析器
│       │   ├── juejin.py     # 掘金解析器
│       │   ├── csdn.py       # CSDN 解析器
│       │   └── generic.py    # 通用网页解析器
│       └── renderers/
│           └── markdown.py   # 最终 Markdown 文件模板
└── tests/
    ├── fixtures/             # 各平台 HTML 测试样例
    └── test_*.py             # 单元测试和 CLI 测试
```

## 核心文件说明

| 文件 | 作用 |
| --- | --- |
| `src/pagemd/cli.py` | 定义 `pagemd`、`convert`、`batch`、`config init`、`doctor` 命令，并控制动态进度状态。 |
| `src/pagemd/config.py` | 读取 `.pagemd.toml`，合并默认配置和用户配置。 |
| `src/pagemd/detect.py` | 根据 URL 自动识别 `wechat`、`juejin`、`csdn` 或 `generic`。 |
| `src/pagemd/fetchers/browser.py` | 使用 Camoufox 抓取需要浏览器渲染的页面，当前主要用于微信公众号。 |
| `src/pagemd/fetchers/http.py` | 使用 HTTP 抓取普通网页，当前用于掘金、CSDN 和通用页面。 |
| `src/pagemd/platforms/wechat.py` | 提取微信公众号标题、作者、发布时间、正文、图片和代码块。 |
| `src/pagemd/platforms/base.py` | 提供跨平台正文清洗、图片收集、代码块保留、HTML 转 Markdown 的通用能力。 |
| `src/pagemd/renderers/markdown.py` | 控制最终 `article.md` 的整体格式，包括 front matter、标题、来源信息和正文插入位置。 |
| `src/pagemd/output.py` | 控制输出目录命名、`article.md`、`metadata.json` 写入和内容 hash。 |
| `src/pagemd/assets.py` | 下载图片到本地 `images/`，并把 Markdown 里的远程图片链接改成本地路径。 |
| `src/pagemd/models.py` | 定义标准文章结构，是未来 GitHub 发布和 HaoGit 导入的基础。 |

## 转换流程

```text
URL
  ↓
detect.py 判断平台
  ↓
fetchers/http.py 或 fetchers/browser.py 抓取 HTML
  ↓
platforms/<platform>.py 解析为 Article
  ↓
platforms/base.py 清洗正文并转换 Markdown
  ↓
assets.py 下载图片并改写链接
  ↓
renderers/markdown.py 生成 article.md
  ↓
output.py 写入 article.md、metadata.json、extraction-report.json
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
