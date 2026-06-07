# Roadmap

中文 | English below

MagicMD 的 GitHub Issues 主要留给真实问题：某篇文章转换错了、安装失败、平台页面变了、文档看不懂。内部计划放在这里，避免 Issues 页面变成待办清单。

## v0.1.1 - done

这个版本不做大功能，只补发布后最容易影响新用户体验的地方。

- 优化 npm wrapper 的缺 `uvx` 提示，让用户知道为什么需要 `uv`，以及如何安装。
- 增加 `docs/troubleshooting.md`，集中说明安装、Camoufox、403、视频防盗链、图片失败、批量中断等常见问题。
- 增加 `magicmd doctor --json`，方便脚本、CI 和 Agent Skill 做环境诊断。
- 梳理 `docs/supported-sites.md`，明确微信公众号、掘金、CSDN 和通用网页的支持边界。
- 补充转换效果反馈格式：原文链接、执行命令、`extraction-report.json`、问题截图或 Markdown 片段。

## v0.2

- 增加 Markdown 模板系统，允许配置 front matter、标题、来源信息和图片路径格式。
- 改进批量转换报告，让失败链接、warning 和可疑 Markdown 更容易定位。
- 补充更多真实文章回归样本，优先覆盖微信公众号、掘金和 CSDN。

## v0.3

- 支持 GitHub token，把转换后的文章提交到指定仓库。
- 支持配置目标目录、分支、提交信息和是否自动创建 Pull Request。
- 增加 HaoGit 导入流程的适配说明。

## Later

- 发布和维护 Agent Skill。
- 评估知乎、博客园、少数派等更多平台适配。
- 增加更细的媒体处理策略，例如视频占位、远程链接保留、本地下载失败 fallback。

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

## v0.1.1 - done

This release stays small and focuses on post-release user experience.

- Improve the npm wrapper message when `uvx` is missing.
- Add `docs/troubleshooting.md` for install, Camoufox, 403, video hotlinking, failed images, and interrupted batch runs.
- Add `magicmd doctor --json` for scripts, CI, and Agent Skill diagnostics.
- Polish `docs/supported-sites.md` with clear support boundaries for WeChat, Juejin, CSDN, and generic pages.
- Document the preferred bad-conversion feedback format.

## v0.2

- Add a Markdown template system for front matter, headings, source blocks, and image paths.
- Improve batch reports for failures, warnings, and suspicious Markdown.
- Expand live regression samples for WeChat, Juejin, and CSDN.

## v0.3

- Use a GitHub token to commit converted articles into a configured repository.
- Configure target directory, branch, commit message, and optional Pull Request creation.
- Document the HaoGit import workflow.

## Later

- Publish and maintain the Agent Skill.
- Evaluate more platforms such as Zhihu, CNBlogs, and SSPAI.
- Add more media handling strategies for videos, remote links, and local-download fallback.

## Feedback

Open a GitHub Issue when a real article converts poorly. Helpful reports include:

- Original URL
- Command used
- `extraction-report.json`
- Problematic `article.md` snippet
- Original and converted screenshots
