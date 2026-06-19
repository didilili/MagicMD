# Roadmap

中文 | English below

MagicMD 的 GitHub Issues 主要留给真实问题：某篇文章转换错了、安装失败、平台页面变了、文档看不懂。内部计划放在这里，避免 Issues 页面变成待办清单。

## 已完成

### v0.1.x

- 打磨微信公众号、掘金、CSDN 的基础转换效果。
- 补齐批量转换、回归样本、质量报告和 release checklist。
- 增加 `docs/troubleshooting.md`，集中说明安装、Camoufox、403、视频防盗链、图片失败、批量中断等常见问题。
- 增加 `magicmd doctor --json`，方便脚本、CI 和 Agent Skill 做环境诊断。

### v0.2.x

- 增加 Markdown 模板系统，支持配置 front matter、标题、来源信息、文件命名和媒体路径。
- 增加在线配置生成器，帮助用户生成 `.magicmd.toml`。
- 梳理 PyPI、npm、Agent Skill、GitHub Pages 和自定义域名发布流程。

### v0.3.x

- 增加稳定 Python SDK：`from magicmd import convert_article`。
- CLI 单篇转换复用 SDK，避免 CLI 和 SDK 各跑一套逻辑。
- 返回结构化 `ArticleConversionResult`，包含 Markdown、metadata、report、warnings、images、content hash 和 package path。
- 增加明确错误类型：`UnsupportedPlatformError`、`FetchError`、`ParseError`、`MediaDownloadError`、`ConversionError`。

### v0.4.x

- CLI 默认改为中文优先提示，并支持通过 `[ui] language = "en-US"` 切回英文输出。
- 官网补齐中英文双语文档、配置生成器语言选项和 Agent Skill 使用说明。
- Agent Skill 文档改为面向 Codex、Claude Code 等支持 Skill 的 Agent 工具，并支持用一句话描述安装需求。
- 增加 Ruff、Prettier、lint-staged、Husky 和 commitlint 工作流，降低协作和发布时的格式风险。

### v0.5.x

- 建立更系统的真实站点回归集，优先覆盖微信公众号、掘金和 CSDN 的中文技术文章。
- 把 Agent 使用入口继续产品化：让用户能用一句话完成安装、转换、批量整理和结果检查。
- 优化官网首页和快速开始，让新用户更快理解“中文文章归档到 Markdown 内容包”的核心场景。
- 增加发布后 smoke test checklist，覆盖 PyPI、npm、GitHub Release 和 Skill 安装路径。
- 评估 PyPI Trusted Publisher 和 npm GitHub Actions 发布流程，减少手动 token 发布和权限切换带来的风险。
- 增加可选 DOCX 导出，并默认保留微信公众号封面图，让归档内容包更完整。

## 下一阶段

### v0.6 - 发布工作流

- 评估 GitHub token 发布器：把转换后的文章提交到指定仓库。
- 支持配置目标目录、分支、提交信息和是否自动创建 Pull Request。
- 先保证它是可选工作流，不影响 MagicMD 的核心转换能力。

## Later

- 维护 Agent Skill，保持它只调用 CLI，不复制转换逻辑。
- 评估知乎、博客园、少数派等更多平台适配。
- 增加更细的媒体处理策略，例如视频占位、远程链接保留、本地下载失败 fallback。
- 建立更系统的真实站点回归集，降低平台改版带来的格式退化。

## Feedback

如果你遇到某篇文章转换不好，再开 GitHub Issue。最好带上：

- 原文链接
- 使用的命令
- 输出目录里的 `extraction-report.json`
- 有问题的 `article.md` 片段
- 原文截图和转换后截图

---

# Roadmap

GitHub Issues are mainly for real user reports: bad conversions, failed installs, platform changes, or confusing docs. Internal planning lives here instead of filling the issue tracker with project chores.

## Done

### v0.1.x

- Improved baseline conversion quality for WeChat, Juejin, and CSDN.
- Added batch conversion, regression samples, quality reports, and release checklists.
- Added `docs/troubleshooting.md` for install, Camoufox, 403, video hotlinking, failed images, and interrupted batch runs.
- Added `magicmd doctor --json` for scripts, CI, and Agent Skill diagnostics.

### v0.2.x

- Added a Markdown template system for front matter, headings, source blocks, output naming, and media paths.
- Added the online config builder for generating `.magicmd.toml`.
- Documented PyPI, npm, Agent Skill, GitHub Pages, and custom-domain release workflows.

### v0.3.x

- Added the stable Python SDK: `from magicmd import convert_article`.
- Reused the SDK from single-article CLI conversion, avoiding duplicated conversion paths.
- Returned structured `ArticleConversionResult` data with Markdown, metadata, report, warnings, images, content hash, and package path.
- Added explicit errors: `UnsupportedPlatformError`, `FetchError`, `ParseError`, `MediaDownloadError`, and `ConversionError`.

### v0.4.x

- Made CLI output Chinese-first by default, with `[ui] language = "en-US"` for English output.
- Added bilingual website docs, a Config Builder language option, and Agent Skill usage guidance.
- Generalized the Agent Skill guide for Codex, Claude Code, and other Skill-capable agent tools, including one-sentence install requests.
- Added Ruff, Prettier, lint-staged, Husky, and commitlint workflows to reduce formatting and collaboration risk.

### v0.5.x

- Build a more systematic live-site regression corpus, prioritizing Chinese technical articles from WeChat, Juejin, and CSDN.
- Productize the Agent entrypoint so users can install, convert, batch organize, and inspect results with short natural-language requests.
- Improve the website homepage and quick start around the core promise: archiving Chinese articles into Markdown content packages.
- Add a post-release smoke test checklist for PyPI, npm, GitHub Release, and Skill installation paths.
- Evaluate PyPI Trusted Publisher and npm GitHub Actions publishing to reduce manual token and permission friction.
- Added optional DOCX export and default WeChat cover-image output so archived content packages are more complete.

## Next

### v0.6 - Publishing workflow

- Evaluate a GitHub token publisher for committing converted articles to a configured repository.
- Support target directory, branch, commit message, and optional Pull Request creation.
- Keep this as an optional workflow, separate from MagicMD's conversion core.

## Later

- Maintain the Agent Skill while keeping it as a CLI workflow, not duplicated converter logic.
- Evaluate more platforms such as Zhihu, CNBlogs, and SSPAI.
- Add more media handling strategies for videos, remote links, and local-download fallback.
- Build a broader live-site regression corpus to reduce format regressions after platform changes.

## Feedback

Open a GitHub Issue when a real article converts poorly. Helpful reports include:

- Original URL
- Command used
- `extraction-report.json`
- Problematic `article.md` snippet
- Original and converted screenshots
