# Changelog

## Unreleased

## v0.7.10 - 2026-08-11

### 中文

- 识别微信公众号使用固定高度和垂直滚动样式模拟的纯文本面板，并转换为保留空行的 `text` 围栏代码块。
- 规则限定于带 `data-autoskip` 标记的纯文本容器，并排除图片、视频、表格及已有代码结构，避免误判滚动图片和普通页面布局。

### English

- Preserved WeChat text panels implemented with fixed-height vertical scrolling as fenced `text` blocks while retaining paragraph spacing.
- Limited detection to text-only containers marked with `data-autoskip`, excluding images, video, tables, and existing code structures to avoid false positives.

## v0.7.9 - 2026-08-11

### 中文

- 扩展 `duplicate_list_marker` 质量检测，识别可视圆点或重复序号与正文、行内代码直接相连的无空格写法。
- 保留普通段落、行内代码、代码块及嵌套列表中的合法符号，避免误报。

### English

- Extended `duplicate_list_marker` quality detection to catch visible bullets and repeated numbers directly attached to text or inline code without whitespace.
- Preserved valid symbols in regular paragraphs, inline code, fenced code blocks, and nested lists to avoid false positives.

## v0.7.8 - 2026-08-11

### 中文

- 修复微信公众号把两位章节序号粘连到图片说明末尾时，序号没有并入后续标题的问题。
- 规则限定于图片说明、无空格两位序号和紧邻标题的组合，保护年份及带空格的普通图片编号。

### English

- Fixed two-digit WeChat section numbers being left attached to an image caption instead of merged into the following heading.
- Limited the repair to image captions with an unspaced two-digit suffix immediately before a heading, preserving years and ordinary spaced figure numbers.

## v0.7.7 - 2026-08-11

### 中文

- 修复微信公众号视觉章节序号以独立数字段落紧邻已识别标题时，生成孤立序号而未组成规范 Markdown 标题的问题。
- 合并后保留原有标题层级与章节序号，避免重复编号，并保护超过两位的普通数字段落。

### English

- Fixed orphan section numbers when a standalone numeric WeChat block immediately precedes an already detected Markdown heading.
- The normalized heading preserves its original level and section number, avoids duplicate numbering, and leaves ordinary numeric paragraphs longer than two digits unchanged.

## v0.7.6 - 2026-08-11

### 中文

- 修复可视圆点或有序编号后未留空格时，真实 HTML 列表项仍可能生成重复 Markdown 列表标记的问题。
- 扩展无空格列表前缀回归测试，并继续保护普通段落、行内代码和代码块中的合法标记。

### English

- Fixed duplicate Markdown list markers when visible bullets or ordered-number prefixes are directly adjacent to list-item text without whitespace.
- Extended regressions for no-space list prefixes while preserving valid markers in regular paragraphs, inline code, and code blocks.

## v0.7.5 - 2026-08-11

### 中文

- 修复源 HTML 列表项同时包含语义列表结构和可视圆点或序号时，生成 `- •` 或 `1. 1.` 等重复列表标记的问题。
- 新增 `duplicate_list_marker` 质量检测，并保护普通段落、行内代码、代码块和嵌套列表中的合法标记。

### English

- Fixed duplicate list markers such as `- •` and `1. 1.` when source HTML list items contain both semantic list structure and visible bullet or number prefixes.
- Added `duplicate_list_marker` quality detection while preserving valid markers in regular paragraphs, inline code, code blocks, and nested lists.

## v0.7.4 - 2026-08-09

### 中文

- 修复文章正文标题层级跳跃的问题；当源 HTML 从 `h2` 直接跳到 `h4`、`h5` 等更深层级时，MagicMD 现在会保留原有父子关系并压平缺失层级，生成连续的 Markdown 标题结构。
- 增加微信公众号标题断层回归测试，覆盖子标题、孙级标题、同级标题和返回较浅层级的组合。

### English

- Fixed skipped heading levels in article bodies. When source HTML jumps directly from `h2` to `h4`, `h5`, or deeper levels, MagicMD now preserves the original parent-child relationships while producing a continuous Markdown heading hierarchy.
- Added a WeChat regression case covering child, grandchild, sibling, and shallower heading transitions.

## v0.7.3 - 2026-07-29

### 中文

- 修复微信公众号正文使用视觉上为普通段落的 `h1` 标签时被错误写入文章目录的问题；MagicMD 现在会根据正文字号、字重和颜色还原这类段落，同时保留真正的一级标题及其层级。
- 修复图片夹在相邻加粗文本之间时强调边界被破坏的问题，并清理独立的 `**` 标记。
- 修复合法行内代码触发加粗边界或强调符号质量误报的问题。

### English

- Fixed WeChat body paragraphs encoded as visually plain `h1` elements being added to the article table of contents. MagicMD now restores those elements to paragraphs based on body typography while preserving genuine first-level headings and their hierarchy.
- Preserved emphasis boundaries when images appear between adjacent strong spans and removed standalone `**` markers.
- Prevented valid inline code from triggering false strong-boundary or emphasis-marker quality issues.

## v0.7.2 - 2026-07-25

### 中文

- 新增 `ConvertedVideo` 和 `ArticleConversionResult.videos`，SDK 现在会返回视频来源、Markdown 路径、本地文件路径和扩展名，方便业务系统明确选择归档或不归档视频。
- 加固视频下载重试、重复来源复用、路径冲突检测和内容包目录边界，避免覆盖已有视频或返回越界文件路径。
- 系统化修复采集 Markdown 中的加粗边界、游离强调符号、空图片、图片外层强调、转义加粗、裸链接和仅地址代码块等格式问题。
- Markdown 修复会保护行内代码、围栏代码块、嵌套容器、带括号的图片地址与标题以及引用式链接，减少格式清理对原文语义的误伤。
- 扩展质量扫描，识别相对本地视频、失效图片、标题层级跳跃、异常代码语言、外部微信媒体未重写等采集缺陷，并支持安全、幂等的 `repair_markdown_quality()`。
- 修复 npm wrapper 和 `uvx --from magicmd` 可能解析到不兼容 Playwright 版本的问题；npm wrapper 固定请求同版本 Python 包，并在 Windows 上正确调用 `uvx.exe`，发布元数据将 Playwright 约束在与 Camoufox 0.4.11 已验证兼容的 1.60 版本线。
- 新增可选的真实 Camoufox `Browser.new_page()` 冒烟测试入口，用于发布前验证浏览器协议兼容性。

### English

- Added `ConvertedVideo` and `ArticleConversionResult.videos`, exposing each video's source URL, Markdown path, local path, and extension so SDK consumers can explicitly choose whether to archive video files.
- Hardened video retry behavior, duplicate-source reuse, path-collision detection, and package-root containment to avoid overwriting existing videos or returning paths outside the generated package.
- Systematically repaired collected Markdown defects involving strong boundaries, orphan emphasis markers, empty images, emphasized images, escaped strong markers, bare URLs, and address-only code fences.
- Protected inline code, fenced code blocks, nested containers, parenthesized image destinations and titles, and reference-style links from destructive cleanup.
- Expanded quality scanning for relative local videos, broken images, heading-level jumps, suspicious code languages, unreplaced external WeChat media, and other ingestion defects, with safe and idempotent `repair_markdown_quality()` support.
- Fixed npm wrapper and `uvx --from magicmd` installs resolving an incompatible Playwright version; the npm wrapper now requests the same-version Python package and correctly invokes `uvx.exe` on Windows, while published metadata constrains Playwright to the 1.60 line verified with current Camoufox 0.4.11.
- Added an opt-in real Camoufox `Browser.new_page()` smoke test for pre-release browser-protocol verification.

## v0.5.0 - 2026-06-19

### 中文

- 新增可选 DOCX 导出：`magicmd convert URL --format docx` 或 `[docx] enabled = true` 会在保留 Markdown 内容包的同时额外生成 `article.docx`，导出由 Pandoc 执行，并支持配置 `pandoc_path` 和 `reference_doc`。
- 修复 `--overwrite` 覆盖同名内容包时旧图片、旧 DOCX 等生成文件可能残留的问题；现在会先清理已有生成包，再写入本次转换结果。
- 新增微信封面图元数据提取和默认输出，生成的 Markdown 内容包会更完整地保留公众号文章卡片信息。
- 新增真实站点回归清单和 dry run 记录，覆盖微信公众号、掘金、CSDN 等样本，便于发布前检查解析质量是否退化。
- 新增手动触发的 PyPI / npm Trusted Publishing workflow，并补齐发布自动化说明和发布后 smoke test 清单。
- 优化官网首页、Agent Skill 文档和配置生成器体验；配置生成器在宽屏下保留更接近文档页的左右留白。

### English

- Added optional DOCX export: `magicmd convert URL --format docx` or `[docx] enabled = true` keeps the Markdown package and also generates `article.docx` through Pandoc, with configurable `pandoc_path` and `reference_doc`.
- Fixed stale generated files when `--overwrite` replaces an existing package; MagicMD now clears the old package before writing the current conversion result.
- Added WeChat cover-image metadata extraction and default output so Markdown packages preserve more of the original article card.
- Added live-site regression manifests and dry-run records for WeChat, Juejin, CSDN, and related samples, making pre-release quality checks more systematic.
- Added a manually triggered PyPI / npm Trusted Publishing workflow, plus release automation notes and a post-release smoke test checklist.
- Improved the website homepage, Agent Skill docs, and Config Builder experience; the Config Builder now keeps more document-like side gutters on wide screens.

## v0.4.0 - 2026-06-17

### 中文

- CLI 终端提示默认改为中文优先，并新增 `[ui] language = "en-US"` 配置，英文用户可以显式切回英文输出。
- 配置生成器新增终端语言选项；该选项只控制 CLI 进度和结果提示，不改变 Markdown front matter 字段名或来源信息块模板。
- 官网新增中英文双语文档入口，补齐快速开始、配置、SDK、支持站点、故障排查和 Agent Skill 使用说明。
- Agent Skill 文档改为面向 Codex、Claude Code 等支持 Skill 的 Agent 工具，支持用一句话描述安装需求，同时保留手动安装命令作为兜底。
- 新增 Ruff、Prettier、lint-staged、Husky 和 commitlint 工作流，提交前自动格式化 staged 文件，并继续规范 commit message。

### English

- CLI terminal messages now default to Chinese-first output. English users can set `[ui] language = "en-US"` to keep English CLI progress and result messages.
- Added a terminal-language option to the Config Builder. This only controls CLI progress/result messages and does not rename Markdown front matter fields or the source block template.
- Added bilingual website documentation covering quick start, config, SDK usage, supported sites, troubleshooting, and Agent Skill usage.
- Generalized the Agent Skill guide for Codex, Claude Code, and other Skill-capable agent tools, including a one-sentence install request plus the manual command as a fallback.
- Added Ruff, Prettier, lint-staged, Husky, and commitlint workflows so staged files are formatted before commit while commit messages stay conventional.

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
