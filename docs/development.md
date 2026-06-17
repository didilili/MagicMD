# MagicMD 开发文档 / Development Notes

这份文档面向准备修改 MagicMD 源码的维护者。用户上手信息放在根目录 [README.md](../README.md)，站点支持状态放在 [docs/supported-sites.md](./supported-sites.md)。

This document is for maintainers who want to change MagicMD internals. User-facing usage lives in the root [README.md](../README.md), and site support status lives in [docs/supported-sites.md](./supported-sites.md).

## 项目结构 / Project Structure

```text
magicmd/
├── README.md                  # 中文说明文档
├── README_EN.md               # English documentation
├── CHANGELOG.md               # 中英文版本变更记录
├── LICENSE                    # MIT 开源许可证
├── SKILL.md                   # 兼容入口；正式 Skill 位于 skills/magicmd/
├── .magicmd.example.toml       # MagicMD 配置示例
├── pyproject.toml             # Python 包配置、依赖和 CLI 入口
├── uv.lock                    # uv 锁定依赖版本
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions：测试、lint 和构建
├── docs/
│   ├── MagicMD-v0.1-design.md
│   ├── MagicMD-v0.1-implementation-plan.md
│   ├── development.md
│   ├── integrations/
│   │   ├── python-sdk.md
│   │   └── haogit-import.md
│   ├── releases/
│   ├── supported-sites.md
│   └── wechat-regression-corpus.md
├── examples/
│   └── python/                # SDK 接入示例
├── npm/
│   └── magicmd/               # npm wrapper，转发到 PyPI 版 CLI
│       ├── package.json
│       ├── README.md
│       └── bin/
│           └── magicmd.js
├── skills/
│   └── magicmd/               # 可安装的 Agent Skill
│       ├── SKILL.md
│       └── agents/
│           └── openai.yaml
├── samples/                   # 真实站点验证 URL 样本
├── src/
│   └── magicmd/
│       ├── __init__.py
│       ├── sdk.py
│       ├── cli.py
│       ├── config.py
│       ├── detect.py
│       ├── models.py
│       ├── output.py
│       ├── quality.py
│       ├── assets.py
│       ├── diagnostics.py
│       ├── fetchers/
│       │   ├── http.py
│       │   └── browser.py
│       ├── platforms/
│       │   ├── base.py
│       │   ├── wechat.py
│       │   ├── juejin.py
│       │   ├── csdn.py
│       │   ├── generic.py
│       │   ├── registry.py
│       │   └── shared/
│       │       ├── content.py
│       │       ├── markdown.py
│       │       └── metadata.py
│       ├── renderers/
│       │   └── markdown.py
│       └── templates/
│           └── magicmd.example.toml
└── tests/
    ├── fixtures/
    ├── test_platform_wechat.py
    ├── test_platform_juejin.py
    ├── test_platform_csdn.py
    ├── test_platform_generic.py
    └── test_*.py
```

## 核心模块 / Core Modules

| 文件                                       | 作用                                                                                                            |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `src/magicmd/__init__.py`                  | 对外导出稳定 Python SDK 入口、结果模型和错误类型。                                                              |
| `src/magicmd/sdk.py`                       | 定义 `convert_article()`、`ArticleConversionResult`、`ConvertedImage` 和 SDK 错误映射；CLI 单篇转换也复用这里。 |
| `src/magicmd/cli.py`                       | 定义 `magicmd`、`convert`、`batch`、`config init`、`doctor` 命令，并控制动态进度状态。                          |
| `src/magicmd/config.py`                    | 读取 `.magicmd.toml`，合并默认配置和用户配置。                                                                  |
| `src/magicmd/detect.py`                    | 根据 URL 自动识别 `wechat`、`juejin`、`csdn` 或 `generic`。                                                     |
| `src/magicmd/models.py`                    | 定义 `Article`、`ImageAsset`、`ExtractionInfo` 等标准数据结构。                                                 |
| `src/magicmd/output.py`                    | 控制输出包命名、`output.naming` 文件名模板、Markdown/metadata 写入和内容 hash。                                 |
| `src/magicmd/assets.py`                    | 下载图片到本地 `images/`，并把 Markdown 里的远程图片链接改成本地路径。                                          |
| `src/magicmd/diagnostics.py`               | 写入 `debug.html` 和 `extraction-report.json`。                                                                 |
| `src/magicmd/quality.py`                   | 扫描 Markdown 质量疑点，并为 batch 命令生成 `batch-report.json`、`batch-report.md`。                            |
| `src/magicmd/fetchers/http.py`             | 使用 HTTP 抓取普通网页。                                                                                        |
| `src/magicmd/fetchers/browser.py`          | 使用 Camoufox 抓取需要浏览器渲染的页面。                                                                        |
| `src/magicmd/platforms/registry.py`        | 集中维护支持平台、URL 匹配规则、默认抓取模式和解析器入口。                                                      |
| `src/magicmd/platforms/wechat.py`          | 微信公众号解析器。                                                                                              |
| `src/magicmd/platforms/juejin.py`          | 掘金解析器。                                                                                                    |
| `src/magicmd/platforms/csdn.py`            | CSDN 解析器。                                                                                                   |
| `src/magicmd/platforms/generic.py`         | 通用网页解析器。                                                                                                |
| `src/magicmd/platforms/base.py`            | 兼容入口，继续导出平台解析器使用的通用函数。                                                                    |
| `src/magicmd/platforms/shared/content.py`  | 正文 DOM 清洗、图片识别、代码块保留。                                                                           |
| `src/magicmd/platforms/shared/markdown.py` | HTML 转 Markdown 和 Markdown 后处理。                                                                           |
| `src/magicmd/platforms/shared/metadata.py` | 元数据、脚本变量、文本和时间提取工具。                                                                          |
| `src/magicmd/renderers/markdown.py`        | 控制最终 `article.md` 的整体格式，包括 front matter、标题、来源信息和正文插入位置。                             |
| `npm/magicmd/bin/magicmd.js`               | npm wrapper 入口，调用 `uvx --from magicmd magicmd ...`，不复制 Python 转换逻辑。                               |
| `docs/integrations/python-sdk.md`          | SDK 字段、错误、媒体路径和后端接入契约。                                                                        |
| `docs/integrations/haogit-import.md`       | HaoGit/CMS 风格导入建议，只描述映射和流程，不写业务系统专属逻辑。                                               |
| `examples/python/convert_to_json.py`       | 调用 SDK 并输出完整 JSON 结果。                                                                                 |
| `examples/python/convert_for_cms.py`       | 演示把图片复制到业务 media 目录并重写 Markdown 链接。                                                           |

## 转换流程 / Conversion Flow

```text
URL
  ↓
detect.py 判断平台
  ↓
fetchers/http.py 或 fetchers/browser.py 抓取 HTML
  ↓
platforms/<platform>.py 解析为 Article
  ↓
platforms/shared/* 清洗正文并转换 Markdown
  ↓
output.py 写入初始内容包（output_dir 有值时）
  ↓
assets.py 下载图片并改写链接（output_dir 有值时）
  ↓
renderers/markdown.py 生成最终 Markdown
  ↓
output.py / diagnostics.py 写入 article.md、metadata.json、extraction-report.json
  ↓
sdk.py 返回 ArticleConversionResult
```

## 添加新平台 / Adding a Platform

1. 在 `src/magicmd/platforms/` 新增平台解析器。
2. 在 `src/magicmd/platforms/registry.py` 注册 URL 匹配规则、默认抓取方式、等待选择器和解析器。
3. 在 `tests/test_detect.py` 增加平台识别测试。
4. 新增 `tests/test_platform_<name>.py`，覆盖标题、作者、发布时间、正文、图片、代码块和链接。
5. 更新 [docs/supported-sites.md](./supported-sites.md) 和 README 的支持矩阵。
6. 如有真实样本，加入 `samples/` 或 `tests/fixtures/site_validation_manifest.json`。

## 验证命令 / Verification Commands

常规检查：

```bash
uv run ruff check .
uv run pytest
uv run magicmd doctor
uv run magicmd doctor --json
```

构建检查：

```bash
rm -f dist/*.whl dist/*.tar.gz
uv build
uvx twine check dist/*
```

真实样本回归：

```bash
uv run magicmd batch samples/juejin-homepage-5.txt -o output/juejin-check --skip-existing
uv run magicmd batch samples/csdn-complex-10.txt -o output/csdn-check --skip-existing
```

如果修改了 README，必须同时更新 `README.md` 和 `README_EN.md`。

如果修改公开 SDK 字段或错误类型，必须同步更新：

- [README.md](../README.md)
- [README_EN.md](../README_EN.md)
- [docs/integrations/python-sdk.md](./integrations/python-sdk.md)
- `tests/test_sdk.py`
