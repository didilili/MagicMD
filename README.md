# MagicMD

中文 | [English](./README_EN.md)

MagicMD 是一个把公开文章链接一键转换为 Markdown 内容包的 CLI 工具。

它参考了单平台文章转换工具的有效经验，但目标更完整：更好的架构、更强的配置能力、多平台适配、标准化元数据，以及后续发布到 GitHub 或接入 HaoGit 的扩展空间。

## 特性

- 输入一个文章 URL，输出 Markdown 内容包。
- 支持微信公众号、掘金、CSDN 和通用公开文章页面。
- 支持批量 URL 转换。
- 支持可配置的 Markdown front matter 和输出结构。
- 自动下载文章图片，并改写 Markdown 图片链接为本地路径。
- 生成 `metadata.json`，方便后续发布到 GitHub、HaoGit 或其他网站。
- 生成 extraction report，方便排查抓取和解析问题。
- 批量转换自动生成 `batch-report.json` 和 `batch-report.md`，方便快速定位失败链接、解析 warning 和 Markdown 质量疑点。
- 内置 `SKILL.md`，可以作为 Agent Skill 使用。

## 安装

```bash
uv sync --extra dev
```

## 使用

单篇文章转换：

```bash
uv run magicmd "https://mp.weixin.qq.com/s/example"
```

显式使用 `convert` 命令：

```bash
uv run magicmd convert "https://juejin.cn/post/example" -o output/
```

批量转换：

```bash
uv run magicmd batch urls.txt -o output/
```

批量转换结束后，会在输出目录生成：

```text
output/
├── batch-report.json
└── batch-report.md
```

初始化配置：

```bash
uv run magicmd config init
```

检查运行环境：

```bash
uv run magicmd doctor
```

## 输出结构

```text
output/
├── batch-report.json          # batch 命令生成，机器可读质量报告
├── batch-report.md            # batch 命令生成，人工阅读质量报告
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
magicmd/
├── README.md                 # 中文说明文档
├── README_EN.md              # English documentation
├── CHANGELOG.md              # 中英文版本变更记录
├── LICENSE                   # MIT 开源许可证
├── SKILL.md                  # Agent Skill 使用说明
├── .magicmd.example.toml      # MagicMD 配置示例
├── pyproject.toml            # Python 包配置、依赖和 CLI 入口
├── uv.lock                   # uv 锁定依赖版本
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions：测试、lint 和构建
├── docs/
│   ├── MagicMD-v0.1-design.md
│   ├── MagicMD-v0.1-implementation-plan.md
│   └── wechat-regression-corpus.md
├── src/
│   └── magicmd/
│       ├── cli.py            # CLI 命令入口和转换编排
│       ├── config.py         # 配置文件加载与默认配置
│       ├── detect.py         # 根据 URL 判断平台
│       ├── models.py         # Article、ImageAsset、ExtractionInfo 数据模型
│       ├── output.py         # 输出目录、article.md 和 metadata.json 写入
│       ├── quality.py        # 批量质量报告和 Markdown 疑点扫描
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
│       ├── renderers/
│       │   └── markdown.py   # 最终 Markdown 文件模板
│       └── templates/
│           └── magicmd.example.toml # wheel 内置配置模板
└── tests/
    ├── fixtures/             # 各平台 HTML 测试样例和微信回归样本清单
    └── test_*.py             # 单元测试和 CLI 测试
```

## 核心文件说明

| 文件 | 作用 |
| --- | --- |
| `src/magicmd/cli.py` | 定义 `magicmd`、`convert`、`batch`、`config init`、`doctor` 命令，并控制动态进度状态。 |
| `src/magicmd/config.py` | 读取 `.magicmd.toml`，合并默认配置和用户配置。 |
| `src/magicmd/detect.py` | 根据 URL 自动识别 `wechat`、`juejin`、`csdn` 或 `generic`。 |
| `src/magicmd/fetchers/browser.py` | 使用 Camoufox 抓取需要浏览器渲染的页面，当前主要用于微信公众号。 |
| `src/magicmd/fetchers/http.py` | 使用 HTTP 抓取普通网页，当前用于掘金、CSDN 和通用页面。 |
| `src/magicmd/platforms/wechat.py` | 提取微信公众号标题、作者、发布时间、正文、图片和代码块。 |
| `src/magicmd/platforms/base.py` | 提供跨平台正文清洗、图片收集、代码块保留、HTML 转 Markdown 的通用能力。 |
| `src/magicmd/renderers/markdown.py` | 控制最终 `article.md` 的整体格式，包括 front matter、标题、来源信息和正文插入位置。 |
| `src/magicmd/output.py` | 控制输出目录命名、`article.md`、`metadata.json` 写入和内容 hash。 |
| `src/magicmd/quality.py` | 扫描 Markdown 质量疑点，并为 batch 命令生成 `batch-report.json`、`batch-report.md`。 |
| `src/magicmd/assets.py` | 下载图片到本地 `images/`，并把 Markdown 里的远程图片链接改成本地路径。 |
| `src/magicmd/models.py` | 定义标准文章结构，是未来 GitHub 发布和 HaoGit 导入的基础。 |

## v0.1 质量基线

当前 v0.1 基线记录在 [CHANGELOG.md](./CHANGELOG.md)。微信公众号真实样本回归说明在 [docs/wechat-regression-corpus.md](./docs/wechat-regression-corpus.md)，样本清单位于 [tests/fixtures/wechat_regression_manifest.json](./tests/fixtures/wechat_regression_manifest.json)。

建议每次修改微信公众号解析逻辑后执行：

```bash
uv run pytest -q
uv run ruff check .
uv run magicmd batch urls-regression.txt -o output/wechat-regression-check
```

然后检查 `output/wechat-regression-check/batch-report.md`。

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

示例配置文件：[.magicmd.example.toml](./.magicmd.example.toml)

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

当前已生效的配置：

| 配置 | 说明 |
| --- | --- |
| `output.directory` | 未传 `--output` 时使用的默认输出目录。 |
| `output.overwrite` | 是否覆盖同名输出包。 |
| `output.save_debug_html` | `always`、`on_failure`、`never`，控制是否保存 `debug.html`。 |
| `markdown.front_matter` | `yaml` 或 `none`，控制是否输出 YAML front matter。 |
| `markdown.include_source_block` | 控制标题下方的来源信息块。 |
| `markdown.heading_offset` | 统一调整 Markdown 标题层级。 |
| `markdown.template` | `default` 或 `clean`；`clean` 会省略来源信息块。 |
| `images.download` | 是否下载图片。 |
| `images.directory` | 图片保存目录。 |
| `images.filename_pattern` | 图片文件命名格式。 |
| `fetch.timeout_seconds` | HTTP 抓取超时时间。 |
| `fetch.user_agent` | HTTP 抓取 User-Agent。 |
| `platforms.<name>.enabled` | 是否启用某个平台。 |
| `platforms.<name>.browser` | 使用 `http` 或 `camoufox` 抓取。 |
| `platforms.<name>.wait_selector` | 浏览器抓取时等待的选择器。 |

`images.concurrency` 目前保留为后续并发下载配置，当前下载仍按顺序执行。

## Agent Skill

仓库内置 [SKILL.md](./SKILL.md)。支持 Skill 的 Agent 可以根据这份说明调用 MagicMD，把公开文章链接转换为 Markdown 内容包。

## 安全边界

MagicMD 只处理公开文章页面。它不会绕过登录、付费墙、私有内容、验证码或平台访问限制。

## 路线图

- 增强微信公众号真实页面解析稳定性。
- 扩充微信公众号回归样本并持续降低 `batch-report.md` 中的质量疑点。
- 增强掘金、CSDN 真实页面解析质量。
- 增加 Markdown 模板系统。
- 增加 GitHub 发布能力。
- 增加 HaoGit 导入能力。

## 维护规则

README 默认中文，英文版本放在根目录 [README_EN.md](./README_EN.md)。之后修改 README 时，中英文两个文件需要一起更新，避免两种语言版本出现功能描述不一致。
