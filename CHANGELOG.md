# Changelog

## v0.1.0 - 2026-06-06

### 中文

PageMD v0.1.0 固化为可用的独立 CLI 基线，重点覆盖公开文章链接到 Markdown 内容包的转换流程。

- 支持单篇 URL 转换和批量 URL 转换。
- 支持微信公众号、掘金、CSDN 和通用公开文章页面。
- 微信公众号解析已覆盖视频占位与本地下载、图片懒加载、动图占位过滤、富文本加粗清洗、非代码 `pre` 文本、块级链接边界、推荐阅读区等真实样例问题。
- 输出 `article.md`、`metadata.json`、`extraction-report.json` 和本地媒体目录。
- 批量转换后自动生成 `batch-report.json` 和 `batch-report.md`，用于快速定位失败链接、解析 warning 和 Markdown 质量疑点。
- 建立微信公众号回归样本清单：`tests/fixtures/wechat_regression_manifest.json`。

### English

PageMD v0.1.0 is the first usable standalone CLI baseline for converting public article URLs into Markdown content packages.

- Supports single URL conversion and batch URL conversion.
- Supports WeChat public account articles, Juejin, CSDN, and generic public article pages.
- The WeChat parser covers real-world formatting issues around video placeholders and local downloads, lazy images, decorative GIF filtering, rich-text bold cleanup, non-code `pre` text, block-link boundaries, and recommendation sections.
- Outputs `article.md`, `metadata.json`, `extraction-report.json`, and local media directories.
- Batch conversion now generates `batch-report.json` and `batch-report.md` for failed URLs, extraction warnings, and Markdown quality signals.
- Adds the WeChat regression corpus manifest: `tests/fixtures/wechat_regression_manifest.json`.
