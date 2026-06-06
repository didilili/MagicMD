# Changelog

## v0.1.0 - 2026-06-06

### 中文

MagicMD v0.1.0 固化为可用的独立 CLI 基线，重点覆盖公开文章链接到 Markdown 内容包的转换流程。

- 支持单篇 URL 转换和批量 URL 转换。
- 支持微信公众号、掘金、CSDN 和通用公开文章页面。
- 微信公众号解析已覆盖视频占位与本地下载、图片懒加载、动图占位过滤、富文本加粗清洗、非代码 `pre` 文本、块级链接边界、推荐阅读区等真实样例问题。
- 掘金解析已覆盖真实首页样本和复杂技术文章样本，包含图片下载、外链还原、代码块保留和标题层级归一化。
- CSDN 解析已覆盖 10 篇复杂真实样本，并人工确认代码块错位、孤立数字、Mermaid/SVG 图、站内目录死链和代码控件噪声等问题。
- 输出 `article.md`、`metadata.json`、`extraction-report.json` 和本地媒体目录。
- 批量转换后自动生成 `batch-report.json` 和 `batch-report.md`，用于快速定位失败链接、解析 warning 和 Markdown 质量疑点。
- 浏览器抓取层会对瞬时 Camoufox/Playwright 失败自动重试一次，降低批量转换中的偶发中断。
- 建立微信公众号回归样本清单：`tests/fixtures/wechat_regression_manifest.json`。
- 建立跨站点验证清单：`tests/fixtures/site_validation_manifest.json`。

### English

MagicMD v0.1.0 is the first usable standalone CLI baseline for converting public article URLs into Markdown content packages.

- Supports single URL conversion and batch URL conversion.
- Supports WeChat public account articles, Juejin, CSDN, and generic public article pages.
- The WeChat parser covers real-world formatting issues around video placeholders and local downloads, lazy images, decorative GIF filtering, rich-text bold cleanup, non-code `pre` text, block-link boundaries, and recommendation sections.
- The Juejin parser has been validated against live homepage samples and complex technical articles, covering image download, external-link restoration, code blocks, and heading-depth normalization.
- The CSDN parser has been validated against ten complex live samples, with manual review for code-block collisions, stray numeric markers, Mermaid/SVG diagrams, generated table-of-contents links, and code-widget noise.
- Outputs `article.md`, `metadata.json`, `extraction-report.json`, and local media directories.
- Batch conversion now generates `batch-report.json` and `batch-report.md` for failed URLs, extraction warnings, and Markdown quality signals.
- Browser fetching now retries transient Camoufox/Playwright failures once, reducing intermittent interruptions during batch conversion.
- Adds the WeChat regression corpus manifest: `tests/fixtures/wechat_regression_manifest.json`.
- Adds the cross-site validation manifest: `tests/fixtures/site_validation_manifest.json`.
