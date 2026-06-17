# Live Regression Runs

中文 | English below

这份文档说明如何维护和运行 MagicMD 的真实站点回归样本。它和单元测试不同：单元测试使用本地 fixture，必须稳定、快速、可在 CI 中运行；真实站点回归依赖公开网页，可能受网络、平台风控、页面改版影响，所以默认只做人工或本地维护者验证。

统一样本清单位于：

```text
tests/fixtures/live_regression_manifest.json
```

## 为什么需要统一清单

MagicMD 面向微信公众号、掘金、CSDN 和通用公开文章页面。真实站点经常会改 DOM、图片懒加载、跳转链接、代码块结构和风控策略。统一清单的作用是：

- 记录哪些公开文章代表了重要格式风险。
- 标注每篇文章重点检查什么，例如视频、图片、代码块、链接、metadata 或报告。
- 让维护者在修改解析器、Markdown 清洗、媒体下载或批量报告后，有一套可重复的人工验证入口。
- 避免把私有链接、登录态页面、token、cookie 或账号相关内容放进仓库。

## 样本字段

每个样本必须包含：

- `id`: 稳定、可读、唯一的样本 ID。
- `platform`: `wechat`、`juejin`、`csdn` 或 `generic`。
- `url`: 公开文章 URL。
- `fetch_mode`: `camoufox` 或 `http`。
- `status`: `candidate`、`converted`、`needs_review` 或 `blocked`。
- `focus`: 这篇样本代表的风险点。
- `checks`: 运行后需要检查的输出面。
- `review_notes`: 人工复核提示。

不要加入：

- 登录后才能访问的页面。
- 付费墙、验证码、私有内容或内部系统链接。
- 包含 token、cookie、账号 ID 或隐私信息的 URL。
- 只能靠特定个人浏览器状态访问的页面。

## 运行方式

从 manifest 生成临时 URL 列表：

```bash
python3 - <<'PY' > /tmp/magicmd-live-regression-urls.txt
import json
from pathlib import Path

manifest = json.loads(Path("tests/fixtures/live_regression_manifest.json").read_text())
for sample in manifest["samples"]:
    if sample["status"] != "blocked":
        print(sample["url"])
PY
```

批量转换：

```bash
uv run magicmd batch /tmp/magicmd-live-regression-urls.txt \
  -o output/live-regression \
  --skip-existing
```

如果只想快速检查正文结构，不想下载图片：

```bash
uv run magicmd batch /tmp/magicmd-live-regression-urls.txt \
  -o output/live-regression-no-images \
  --no-images \
  --skip-existing
```

## 复核重点

每次运行后先看：

```text
output/live-regression/batch-report.md
output/live-regression/batch-report.json
```

然后按 manifest 里的 `checks` 抽查内容包：

- `article.md`: 正文顺序、标题层级、链接范围、代码块、图片位置。
- `metadata.json`: 标题、作者、发布时间、平台、来源链接。
- `extraction-report.json`: warning、失败阶段、抓取方式、媒体下载信息。
- `images/` 或 `videos/`: 是否有本地媒体，Markdown 路径是否能对应。

## 状态更新

- `candidate`: 已加入清单，还没有稳定复核结论。
- `converted`: 最近一次人工复核可接受。
- `needs_review`: 能转换，但有格式疑点或 warning 需要跟踪。
- `blocked`: 当前公开访问不可用，例如平台风控、验证码、链接失效。

如果真实站点改版导致转换退化，不要只改 manifest。应保留失败输出、截图和相关报告，再补一个本地 fixture 单元测试，确保修复能长期保留。

---

# Live Regression Runs

This document explains how to maintain and run MagicMD's live-site regression samples. Unlike unit tests, live regression depends on public web pages and can be affected by network conditions, platform risk controls, and DOM changes. It should be run manually by maintainers, not as a required CI step.

The unified sample manifest lives at:

```text
tests/fixtures/live_regression_manifest.json
```

## Why This Manifest Exists

MagicMD targets WeChat Official Account, Juejin, CSDN, and generic public article pages. These sites can change DOM structure, lazy image loading, redirect links, code block markup, and access controls. The manifest helps maintainers:

- Track public articles that represent important formatting risks.
- Record what each article is meant to check, such as videos, images, code blocks, links, metadata, or reports.
- Re-run a repeatable manual validation set after parser, Markdown cleanup, media download, or batch-report changes.
- Keep private links, login-only pages, tokens, cookies, and account-specific content out of the repository.

## Sample Fields

Each sample must include:

- `id`: stable, readable, unique sample ID.
- `platform`: `wechat`, `juejin`, `csdn`, or `generic`.
- `url`: public article URL.
- `fetch_mode`: `camoufox` or `http`.
- `status`: `candidate`, `converted`, `needs_review`, or `blocked`.
- `focus`: risks represented by this sample.
- `checks`: output surfaces to inspect after conversion.
- `review_notes`: human review guidance.

Do not add:

- Login-only pages.
- Paywalled, CAPTCHA-protected, private, or internal-system links.
- URLs containing tokens, cookies, account IDs, or private data.
- Pages that only work with one maintainer's browser state.

## How To Run

Generate a temporary URL list from the manifest:

```bash
python3 - <<'PY' > /tmp/magicmd-live-regression-urls.txt
import json
from pathlib import Path

manifest = json.loads(Path("tests/fixtures/live_regression_manifest.json").read_text())
for sample in manifest["samples"]:
    if sample["status"] != "blocked":
        print(sample["url"])
PY
```

Run batch conversion:

```bash
uv run magicmd batch /tmp/magicmd-live-regression-urls.txt \
  -o output/live-regression \
  --skip-existing
```

For a faster text-structure check without image downloads:

```bash
uv run magicmd batch /tmp/magicmd-live-regression-urls.txt \
  -o output/live-regression-no-images \
  --no-images \
  --skip-existing
```

## Review Focus

Start with:

```text
output/live-regression/batch-report.md
output/live-regression/batch-report.json
```

Then inspect packages according to each sample's `checks`:

- `article.md`: body order, heading levels, link boundaries, code blocks, image placement.
- `metadata.json`: title, author, publish time, platform, source URL.
- `extraction-report.json`: warnings, failure stage, fetch mode, media download details.
- `images/` or `videos/`: local media presence and Markdown path consistency.

## Status Updates

- `candidate`: added to the manifest, but not yet accepted as a stable baseline.
- `converted`: latest manual review was acceptable.
- `needs_review`: conversion completes, but warnings or formatting issues need tracking.
- `blocked`: public access is currently unavailable because of risk controls, CAPTCHA, or link rot.

When a live-site change causes regression, do not only update the manifest. Preserve the failing output, screenshots, and reports, then add a local fixture unit test so the fix remains stable.
