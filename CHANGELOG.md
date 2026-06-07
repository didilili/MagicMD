# Changelog

## v0.3.0 - 2026-06-08

### 中文

- 新增公开 Python SDK：外部项目现在可以直接 `from magicmd import convert_article`，无需通过 CLI 或 Agent Skill 间接调用。
- 新增结构化返回对象 `ArticleConversionResult`，包含标题、作者、平台、来源链接、发布时间、摘要、Markdown、内容 hash、图片资产、warning、metadata、转换报告和可选内容包目录。
- 新增图片资产对象 `ConvertedImage`，明确区分 `markdown_path` 和 `local_path`：前者表示 Markdown 中实际引用的路径，后者表示本地已下载图片的文件系统路径。
- 新增公开错误类型：`UnsupportedPlatformError`、`FetchError`、`ParseError`、`MediaDownloadError` 和 `ConversionError`，方便 Web 后端和自动化任务按失败阶段处理。
- 支持 `output_dir=None` 的纯内存转换，适合业务系统直接保存 Markdown 和 metadata；传入 `output_dir` 时仍会生成原有内容包。
- CLI 的单篇转换流程改为复用 SDK，不再与 Python API 维护两套转换逻辑。
- README / README_EN 新增 Python SDK 使用说明和错误处理示例。

### English

- Added the public Python SDK: external projects can now call `from magicmd import convert_article` directly without shelling out to the CLI or relying on the Agent Skill.
- Added the structured `ArticleConversionResult` model with title, author, platform, source URL, publish time, excerpt, Markdown, content hash, image assets, warnings, metadata, extraction report, and optional package directory.
- Added `ConvertedImage` and clarified image paths: `markdown_path` is the path referenced by generated Markdown, while `local_path` is the downloaded filesystem path.
- Added public error types: `UnsupportedPlatformError`, `FetchError`, `ParseError`, `MediaDownloadError`, and `ConversionError` for backend-friendly failure handling.
- Added in-memory conversion with `output_dir=None`, while keeping the existing package-writing behavior when `output_dir` is provided.
- Updated the CLI single-conversion path to reuse the SDK instead of maintaining separate conversion logic.
- Added Python SDK usage and error-handling examples to README / README_EN.

## v0.2.0 - 2026-06-07

### 中文

- 新增 v0.2 模板系统实现计划，并在配置示例中补充当前已生效字段说明和下一版命名/Front matter 设计提示。
- 新增 v0.2 配置模型：`output.naming`、`markdown.preset`、自定义 front matter 字段、source block 模板和 `videos` 配置现在可以被 `.magicmd.toml` 正确读取。
- 新增模板变量模块，统一提供 `{title}`、`{slug}`、`{date}`、`{short_hash}` 等字段，并在未知字段时给出清晰错误。
- 让 `output.naming` 开始控制真实输出：内容包目录、Markdown 文件名、metadata 文件名以及批量 `--skip-existing` 检测都会使用配置值。
- 让 `output.naming.report` 控制提取报告文件名，并支持同一套模板变量。
- 让 Markdown front matter、正文标题和来源信息块支持配置模板，便于直接适配个人博客和静态站。
- 让图片和视频 Markdown 路径支持模板配置，文件仍保存到本地媒体目录，Markdown 可写成站点需要的 `/static/...`、`./images/...` 等路径。
- 新增 `plain`、`hugo`、`docusaurus` Markdown 预设，常见发布目标可以一行配置启用，并保留用户显式配置优先级。
- 激活 `.magicmd.example.toml` 和内置配置模板中的 v0.2 字段，`magicmd config init` 生成的示例现在可直接复制修改。

### English

- Added the v0.2 template-system implementation plan and expanded config examples with current-field notes plus upcoming naming/front-matter design hints.
- Added v0.2 config models so `.magicmd.toml` can now read `output.naming`, `markdown.preset`, custom front matter fields, source block templates, and `videos` settings.
- Added a template variable helper for fields such as `{title}`, `{slug}`, `{date}`, and `{short_hash}`, with clear errors for unknown fields.
- Made `output.naming` affect real output: package directories, Markdown filenames, metadata filenames, and batch `--skip-existing` detection now use configured values.
- Made `output.naming.report` control the extraction report filename with the same template variables.
- Made Markdown front matter, title rendering, and the source block configurable for blog and static-site workflows.
- Made image and video Markdown paths configurable while still saving files into local media directories.
- Added `plain`, `hugo`, and `docusaurus` Markdown presets for common publishing targets while keeping explicit user settings in control.
- Activated v0.2 fields in `.magicmd.example.toml` and the packaged config template so `magicmd config init` creates a ready-to-edit example.

## v0.1.2 - 2026-06-07

### 中文

- 新增可安装的 Agent Skill 目录 `skills/magicmd/`，并补充 `agents/openai.yaml`，用于从 GitHub 路径安装 MagicMD Skill。

### English

- Added the installable Agent Skill at `skills/magicmd/` with `agents/openai.yaml` so MagicMD can be installed as a GitHub-hosted skill.

## v0.1.1 - 2026-06-07

### 中文

- 发布 `magicmd@0.1.1` npm wrapper，支持 `npm install -g magicmd` 和 `npx magicmd` 入口，底层转发到 PyPI 版 `magicmd` CLI。
- 优化 npm wrapper 在缺少 `uvx` 时的错误提示，补充 macOS/Linux、Windows 和 PyPI 直装方式。
- 新增 `docs/troubleshooting.md`，集中说明安装、Camoufox、微信访问限制、图片、CSDN/掘金转换问题和反馈格式。
- 新增 `magicmd doctor --json`，为脚本、CI 和 Agent 提供机器可读的环境诊断结果。
- 完善 `docs/supported-sites.md`，按站点说明支持状态、已优化内容、已知限制和反馈格式。

### English

- Published the `magicmd@0.1.1` npm wrapper, enabling `npm install -g magicmd` and `npx magicmd` while forwarding to the PyPI `magicmd` CLI.
- Improved the npm wrapper message when `uvx` is missing, including macOS/Linux, Windows, and direct PyPI install options.
- Added `docs/troubleshooting.md` for install, Camoufox, WeChat access limits, images, CSDN/Juejin conversion issues, and feedback format.
- Added `magicmd doctor --json` for machine-readable diagnostics in scripts, CI, and agents.
- Expanded `docs/supported-sites.md` with per-site status, optimizations, known limits, and feedback guidance.

## v0.1.0 - 2026-06-06

### 中文

MagicMD v0.1.0 固化为可用的独立 CLI 基线，重点覆盖公开文章链接到 Markdown 内容包的转换流程。

- 支持单篇 URL 转换和批量 URL 转换。
- 支持微信公众号、掘金、CSDN 和通用公开文章页面。
- 微信公众号解析已覆盖视频占位与本地下载、图片懒加载、动图占位过滤、富文本加粗清洗、非代码 `pre` 文本、块级链接边界、推荐阅读区等真实样例问题。
- 掘金解析已覆盖真实首页样本和复杂技术文章样本，包含图片下载、外链还原、代码块保留和标题层级归一化。
- CSDN 解析已覆盖 10 篇复杂真实样本，并人工确认代码块错位、孤立数字、Mermaid/SVG 图、站内目录死链和代码控件噪声等问题。
- 输出 `article.md`、`metadata.json`、`extraction-report.json` 和本地媒体目录。
- 平台注册表集中管理 URL 匹配、默认抓取方式、等待选择器和解析器入口，便于后续扩展新站点。
- 浏览器抓取配置已真实生效，支持通过配置控制 Camoufox 等待超时和最大尝试次数。
- 平台通用转换逻辑已从 `platforms/base.py` 拆分到 `platforms/shared/`，并保留 `base.py` 兼容入口，降低后续维护成本。
- 平台测试已按 WeChat、Juejin、CSDN 和 Generic 拆分，便于单站点回归和定位问题。
- 批量转换后自动生成 `batch-report.json` 和 `batch-report.md`，用于快速定位失败链接、解析 warning 和 Markdown 质量疑点。
- 批量报告补充 `platform`、`fetcher`、`stage`、`elapsed_ms`、`max_attempts` 和 `retry_enabled` 等诊断字段，方便定位失败阶段和抓取上下文。
- 批量命令新增 `--skip-existing` 和 `--overwrite`，支持重复跑回归集时跳过已有内容包，或显式覆盖同名输出包。
- 浏览器抓取层会对瞬时 Camoufox/Playwright 失败自动重试一次，降低批量转换中的偶发中断。
- `magicmd doctor` 已升级为环境诊断命令，可检查 Python 版本、MagicMD 版本、配置解析、输出目录可写性、Camoufox 可用性和平台默认抓取方式。
- 根命令新增 `--version`，方便安装后快速确认当前 CLI 版本。
- 已发布到 PyPI，支持通过 `uv tool install magicmd` 或 `pipx install magicmd` 安装。
- 建立微信公众号回归样本清单：`tests/fixtures/wechat_regression_manifest.json`。
- 建立跨站点验证清单：`tests/fixtures/site_validation_manifest.json`。
- 发布前构建检查通过：`uv build`、wheel/sdist 内容检查、临时 wheel 安装 smoke test 和 `twine check` 均已验证。

### English

MagicMD v0.1.0 is the first usable standalone CLI baseline for converting public article URLs into Markdown content packages.

- Supports single URL conversion and batch URL conversion.
- Supports WeChat public account articles, Juejin, CSDN, and generic public article pages.
- The WeChat parser covers real-world formatting issues around video placeholders and local downloads, lazy images, decorative GIF filtering, rich-text bold cleanup, non-code `pre` text, block-link boundaries, and recommendation sections.
- The Juejin parser has been validated against live homepage samples and complex technical articles, covering image download, external-link restoration, code blocks, and heading-depth normalization.
- The CSDN parser has been validated against ten complex live samples, with manual review for code-block collisions, stray numeric markers, Mermaid/SVG diagrams, generated table-of-contents links, and code-widget noise.
- Outputs `article.md`, `metadata.json`, `extraction-report.json`, and local media directories.
- Centralizes URL matching, default fetch mode, wait selectors, and parser entrypoints in a platform registry to make new-site support easier to add.
- Browser fetch configuration is now effective, allowing Camoufox wait timeouts and maximum attempts to be controlled from config.
- Shared platform conversion logic has been split from `platforms/base.py` into `platforms/shared/`, while `base.py` remains as a compatibility entrypoint.
- Platform tests are now split by WeChat, Juejin, CSDN, and Generic coverage to make site-specific regression easier.
- Batch conversion now generates `batch-report.json` and `batch-report.md` for failed URLs, extraction warnings, and Markdown quality signals.
- Batch reports now include diagnostic fields such as `platform`, `fetcher`, `stage`, `elapsed_ms`, `max_attempts`, and `retry_enabled` to make failures easier to locate.
- The batch command now supports `--skip-existing` and `--overwrite` for repeated regression runs and explicit output replacement.
- Browser fetching now retries transient Camoufox/Playwright failures once, reducing intermittent interruptions during batch conversion.
- `magicmd doctor` is now a real runtime diagnostic command that checks Python version, MagicMD version, config parsing, output writability, Camoufox availability, and platform defaults.
- Adds a root `--version` option so installed CLI environments can quickly confirm the active MagicMD version.
- Published to PyPI, with installation via `uv tool install magicmd` or `pipx install magicmd`.
- Adds the WeChat regression corpus manifest: `tests/fixtures/wechat_regression_manifest.json`.
- Adds the cross-site validation manifest: `tests/fixtures/site_validation_manifest.json`.
- Pre-release build checks passed: `uv build`, wheel/sdist content inspection, temporary wheel-install smoke tests, and `twine check` have all been verified.
