# 支持站点 / Supported Sites

中文 | English below

这份文档记录 MagicMD 当前对不同站点的真实支持状态。它不是营销清单，而是用来帮你判断：这个链接适不适合转、转换后哪些地方需要人工检查、出问题时该带什么信息反馈。

MagicMD 只处理公开文章页面。登录、付费墙、验证码、私有内容、App-only 页面和平台风控挑战不属于支持范围。

## 支持矩阵

| 站点                          | 状态       | 默认抓取   | 适合场景                                                             |
| ----------------------------- | ---------- | ---------- | -------------------------------------------------------------------- |
| 微信公众号 `mp.weixin.qq.com` | 稳定主目标 | `camoufox` | 公众号文章归档、图片本地化、后续发布到知识库或网站。                 |
| 掘金 `juejin.cn`              | 实验支持   | `camoufox` | 技术文章归档，重点保留图片、代码块、外链和标题层级。                 |
| CSDN `blog.csdn.net`          | 实验支持   | `camoufox` | 技术文章归档，重点清理代码块、目录链接、Mermaid/SVG 和页面控件噪声。 |
| 通用网页                      | 尽力支持   | `http`     | 标准 `article`、`main` 或 Open Graph 元信息比较完整的公开页面。      |

## 微信公众号

**状态**：稳定主目标。v0.1 的主要验证对象，已经做过多轮真实样本格式修复。

**默认抓取**：`camoufox`，等待 `#js_content`。

**已重点优化**

- 正文、标题、作者、发布时间和来源链接提取。
- 图片懒加载地址识别和本地下载。
- 视频链接提取；能下载时尝试下载，不能下载时保留链接或占位。
- 空动图、动态装饰图、编辑器占位素材过滤。
- 富文本加粗清洗，减少 `推**荐****阅****读**` 这类错位 Markdown。
- 推荐阅读区、块级链接、非代码 `pre` 文本和公众号常见尾部素材处理。
- 批量转换后写入 `batch-report.md` 和 `extraction-report.json`，便于人工复核。

**已知限制**

- 微信风控、验证码、登录限制、只允许微信内打开的文章无法绕过。
- 视频链接可能带防盗链，提取出来后直接在浏览器打开仍可能 403。
- 过期图片、过期动图或平台动态资源可能无法恢复。
- 原文里依赖复杂 CSS 的排版，转换成 Markdown 后只能保留语义结构，不能完全保留视觉布局。

**反馈建议**

如果某篇微信文章转换不理想，请带上原文链接、`extraction-report.json`、有问题的 `article.md` 片段，以及原文和转换后的截图。

## 掘金

**状态**：实验支持。已验证首页样本和复杂技术文章样本。

**默认抓取**：`camoufox`，等待 `article`。普通 HTTP 抓取可能遇到字节 WAF challenge，因此默认走浏览器模式。

**已重点优化**

- 正文、标题、作者和发布时间提取。
- 图片下载到本地 `images/` 目录。
- 代码块保留，减少复制按钮和页面控件干扰。
- 标题层级归一：文章一级标题后，正文标题从合理层级继续，而不是盲目保留网页里的深层级标签。
- 外链还原：尽量从 `title` 或跳转参数中还原真实目标链接，减少打开时进入掘金风险提示页。

**已知限制**

- 掘金页面结构变化后，目录、作者信息或推荐内容可能需要重新适配。
- 某些站内跳转链接本身依赖登录状态，Markdown 里只能保留可见链接。
- 文章中嵌入的互动组件、评论区和动态脚本不属于正文转换目标。

**反馈建议**

链接问题请带上 `article.md` 中的链接片段；代码块问题请带上原文截图和转换后的 Markdown 片段。

## CSDN

**状态**：实验支持。10 篇复杂真实样本已通过默认配置转换并人工确认。

**默认抓取**：`camoufox`，等待 `#content_views`。普通 HTTP 在验证中返回过 521，因此默认走浏览器模式。

**已重点优化**

- 正文、标题、作者和发布时间提取。
- 代码块清理：减少复制按钮、行号、语言标签、AI 写代码控件和孤立数字干扰。
- Mermaid / SVG 图尽量保留为图片或可读结构，避免变成乱码文本。
- 站内目录死链、页内锚点和标题层级做基础清理。
- 页面侧栏、广告、推荐阅读和无关控件尽量剔除。

**已知限制**

- CSDN 文章模板很多，部分代码块由前端脚本重排，仍可能出现错位。
- Mermaid、流程图、架构图如果是脚本动态渲染，Markdown 中可能只能保留图片或近似文本。
- 登录可见内容、付费内容、折叠区动态加载内容不保证完整提取。

**反馈建议**

CSDN 问题最好同时提供原文截图和转换后截图，尤其是代码块、Mermaid/SVG、目录和表格问题。只描述“错了”通常很难复现。

## 通用网页

**状态**：尽力支持。

**默认抓取**：`http`。

**适合页面**

- 页面有标准 `<article>` 或 `<main>`。
- Open Graph 标题、作者、发布时间等元信息比较完整。
- 正文是服务端渲染或普通 HTML。

**不适合页面**

- 登录后才能看正文。
- 内容完全由前端接口异步加载。
- 需要滚动、点击、展开才能看到关键内容。
- 强依赖复杂 CSS、Canvas、WebGL 或交互组件。

通用网页不是“全网保证支持”。如果某个站点经常需要转换，建议后续为它单独写平台适配器。

## 验证命令

继续扩大样本时，可以先跑批量转换：

```bash
uv run magicmd batch urls.txt -o output/site-validation-next --skip-existing
```

如果只想验证正文结构，不想下载图片：

```bash
uv run magicmd batch urls.txt -o output/site-validation-next --no-images --skip-existing
```

检查环境：

```bash
uv run magicmd doctor
uv run magicmd doctor --json
```

显式配置某个站点的抓取方式：

```toml
[platforms.csdn]
enabled = true
browser = "camoufox"
wait_selector = "#content_views"
```

## 反馈格式

如果某篇文章转换不好，建议按这个格式反馈：

```markdown
## 原文链接

https://...

## 使用命令

magicmd "https://..." -o output/

## 问题描述

例如：代码块错位 / 图片缺失 / 链接不能跳转 / 视频打不开 / 标题层级不对

## 附件或片段

- 输出目录里的 `extraction-report.json`
- `article.md` 中有问题的片段
- 原文截图和转换后截图
```

不要上传 token、cookie、私有文章内容或账号信息。

---

# Supported Sites

This document records MagicMD's current real support status. It is here to help you decide whether a URL is a good fit, what to review after conversion, and what to include when reporting a problem.

MagicMD only targets public article pages. Login-only pages, paywalls, CAPTCHA, private content, app-only pages, and platform access challenges are out of scope.

## Support Matrix

| Site                                       | Status                | Default fetcher | Good fit                                                                                         |
| ------------------------------------------ | --------------------- | --------------- | ------------------------------------------------------------------------------------------------ |
| WeChat Official Account `mp.weixin.qq.com` | Stable primary target | `camoufox`      | Article archiving, local images, later publishing to a knowledge base or website.                |
| Juejin `juejin.cn`                         | Experimental support  | `camoufox`      | Technical-article archiving with images, code blocks, external links, and heading structure.     |
| CSDN `blog.csdn.net`                       | Experimental support  | `camoufox`      | Technical-article archiving with code cleanup, TOC links, Mermaid/SVG, and widget noise removal. |
| Generic pages                              | Best effort           | `http`          | Public pages with standard `article`, `main`, or Open Graph metadata.                            |

## WeChat Official Account

**Status**: stable primary target. This is the main v0.1 validation target, with multiple rounds of live formatting fixes.

**Default fetcher**: `camoufox`, waiting for `#js_content`.

**Optimized**

- Body, title, author, publish time, and source URL extraction.
- Lazy-loaded image URL detection and local download.
- Video link extraction; MagicMD attempts downloads when possible and otherwise keeps links or placeholders.
- Filtering for empty GIFs, decorative animated assets, and editor placeholders.
- Rich-text bold cleanup to avoid broken Markdown such as split bold characters.
- Handling for recommendation sections, block links, non-code `pre` text, and common account footer material.
- Batch reports and `extraction-report.json` for review.

**Known limits**

- WeChat risk control, CAPTCHA, login-only pages, and in-WeChat-only articles are not bypassed.
- Video links may still return 403 because of hotlink protection.
- Expired images, GIFs, or dynamic resources may not be recoverable.
- CSS-heavy visual layouts are converted into Markdown semantics, not pixel-perfect page layouts.

**Feedback**

For WeChat issues, include the original URL, `extraction-report.json`, the problematic `article.md` snippet, and before/after screenshots.

## Juejin

**Status**: experimental support. Homepage samples and complex technical samples have been checked.

**Default fetcher**: `camoufox`, waiting for `article`. Plain HTTP can hit a ByteDance WAF challenge, so browser mode is the default.

**Optimized**

- Body, title, author, and publish time extraction.
- Image download into the local `images/` directory.
- Code block preservation with reduced copy-button and page-widget noise.
- Heading normalization so body headings continue from a reasonable level instead of blindly preserving deep webpage tags.
- External-link restoration from `title` attributes or redirect parameters when possible.

**Known limits**

- Page-structure changes may require updates for TOC, author metadata, or recommendation cleanup.
- Some internal links depend on login state and can only be kept as visible links.
- Interactive widgets, comments, and dynamic scripts are not part of article-body conversion.

**Feedback**

For link issues, include the related `article.md` link snippet. For code-block issues, include the original screenshot and converted Markdown snippet.

## CSDN

**Status**: experimental support. Ten complex live samples have been converted with the default configuration and manually reviewed.

**Default fetcher**: `camoufox`, waiting for `#content_views`. Plain HTTP returned 521 during validation, so browser mode is the default.

**Optimized**

- Body, title, author, and publish time extraction.
- Code block cleanup for copy buttons, line counters, language labels, AI-code widgets, and isolated numbers.
- Mermaid / SVG diagrams are preserved as images or readable structures when possible.
- Basic cleanup for dead TOC links, in-page anchors, and heading levels.
- Sidebar, ads, recommendations, and unrelated controls are removed where possible.

**Known limits**

- CSDN has many article templates; code blocks rearranged by frontend scripts may still be wrong.
- Mermaid, flowcharts, and architecture diagrams rendered dynamically may only survive as images or approximate text.
- Login-only content, paid content, and dynamically expanded sections are not guaranteed.

**Feedback**

For CSDN issues, before/after screenshots are especially useful for code blocks, Mermaid/SVG, TOC, and tables. A short "it is wrong" report is usually not enough to reproduce.

## Generic Pages

**Status**: best effort.

**Default fetcher**: `http`.

**Good fit**

- Pages with standard `<article>` or `<main>`.
- Pages with useful Open Graph metadata.
- Server-rendered or ordinary HTML article bodies.

**Poor fit**

- Login-only pages.
- Content loaded entirely from frontend APIs.
- Pages that require scrolling, clicking, or expanding to reveal the article.
- Pages dominated by CSS, Canvas, WebGL, or interactive components.

Generic support does not mean "the whole web is guaranteed." If you often convert one site, it should eventually get its own platform adapter.

## Validation Commands

To expand validation samples:

```bash
uv run magicmd batch urls.txt -o output/site-validation-next --skip-existing
```

To check text structure without downloading images:

```bash
uv run magicmd batch urls.txt -o output/site-validation-next --no-images --skip-existing
```

Check the environment:

```bash
uv run magicmd doctor
uv run magicmd doctor --json
```

Explicit site fetcher configuration:

```toml
[platforms.csdn]
enabled = true
browser = "camoufox"
wait_selector = "#content_views"
```

## Feedback Format

When an article converts poorly, use this format:

```markdown
## Original URL

https://...

## Command

magicmd "https://..." -o output/

## What went wrong

For example: code block mismatch / missing image / broken link / failed video / wrong heading depth

## Attachments or snippets

- `extraction-report.json`
- the problematic `article.md` snippet
- original and converted screenshots
```

Do not upload tokens, cookies, private article content, or account information.
