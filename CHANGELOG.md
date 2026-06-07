# Changelog

## Unreleased

### 中文

- 发布 `magicmd@0.1.0` npm wrapper，支持 `npm install -g magicmd` 和 `npx magicmd` 入口，底层转发到 PyPI 版 `magicmd` CLI。
- 优化 npm wrapper 在缺少 `uvx` 时的错误提示，补充 macOS/Linux、Windows 和 PyPI 直装方式。
- 新增 `docs/troubleshooting.md`，集中说明安装、Camoufox、微信访问限制、图片、CSDN/掘金转换问题和反馈格式。

### English

- Published the `magicmd@0.1.0` npm wrapper, enabling `npm install -g magicmd` and `npx magicmd` while forwarding to the PyPI `magicmd` CLI.
- Improved the npm wrapper message when `uvx` is missing, including macOS/Linux, Windows, and direct PyPI install options.
- Added `docs/troubleshooting.md` for install, Camoufox, WeChat access limits, images, CSDN/Juejin conversion issues, and feedback format.

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
