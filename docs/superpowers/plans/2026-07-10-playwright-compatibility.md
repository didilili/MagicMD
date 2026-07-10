# Playwright Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a release-ready MagicMD v0.7.1 whose published dependency metadata keeps Camoufox 0.4.11 on the verified Playwright 1.60 protocol and whose tests expose future browser-protocol regressions.

**Architecture:** Add a direct Playwright compatibility constraint at the package boundary because `uvx --from magicmd` resolves from published metadata rather than this repository's lock file. Protect that policy with a fast metadata test, and add an opt-in, network-free Camoufox smoke test that exercises the real `Browser.new_page()` protocol boundary. Prepare synchronized Python/npm version metadata and release notes without publishing, tagging, pushing, or changing fetch/parse behavior.

**Tech Stack:** Python 3.11+, Hatch/PEP 621 metadata, uv, pytest/pytest-asyncio, Camoufox, Playwright, npm wrapper

---

### Task 1: Add failing compatibility regression tests

**Files:**

- Modify: `tests/test_project_metadata.py`
- Modify: `tests/test_browser_fetcher.py`

- [ ] **Step 1: Add the publishing-metadata regression test**

Append this test near the existing project metadata tests:

```python
def test_project_metadata_constrains_playwright_for_camoufox():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert "playwright>=1.60,<1.61" in metadata["project"]["dependencies"]
```

- [ ] **Step 2: Run the metadata test and verify the expected red state**

Run:

```bash
uv run pytest tests/test_project_metadata.py::test_project_metadata_constrains_playwright_for_camoufox -q
```

Expected: FAIL because `pyproject.toml` does not yet directly declare `playwright>=1.60,<1.61`.

- [ ] **Step 3: Add the opt-in real-browser smoke test**

Add `import os` above `import pytest`, then append:

```python
@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.skipif(
    os.environ.get("MAGICMD_RUN_BROWSER_SMOKE") != "1",
    reason="set MAGICMD_RUN_BROWSER_SMOKE=1 to run the real Camoufox smoke test",
)
async def test_camoufox_can_create_page():
    async with browser_fetcher.AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()

    assert page is not None
```

- [ ] **Step 4: Run the smoke test against the known-bad dependency and verify red**

Before changing `pyproject.toml`, run:

```bash
MAGICMD_RUN_BROWSER_SMOKE=1 uv run --isolated --no-project \
  --with '.[dev]' \
  --with 'playwright==1.61.0' \
  pytest tests/test_browser_fetcher.py::test_camoufox_can_create_page -q
```

Expected: FAIL at `Browser.new_page()` with `Browser.setDefaultViewport` rejecting `viewport.isMobile`.

- [ ] **Step 5: Confirm the normal test suite still skips the opt-in smoke test**

Run:

```bash
uv run pytest tests/test_browser_fetcher.py -q
```

Expected: `2 passed, 1 skipped`.

- [ ] **Step 6: Commit the regression tests**

```bash
git add docs/superpowers/plans/2026-07-10-playwright-compatibility.md \
  tests/test_project_metadata.py tests/test_browser_fetcher.py
git commit -m "test: 覆盖 Playwright 浏览器协议兼容性"
```

### Task 2: Constrain Playwright in published package metadata

**Files:**

- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Test: `tests/test_project_metadata.py`
- Test: `tests/test_browser_fetcher.py`

- [ ] **Step 1: Add the minimal direct dependency constraint**

Insert the constraint immediately after the Camoufox dependency:

```toml
dependencies = [
  "beautifulsoup4>=4.12",
  "camoufox[geoip]>=0.4",
  "playwright>=1.60,<1.61",
  "chardet>=5.2",
  "httpx>=0.27",
  "markdownify>=0.13",
  "pydantic>=2.8",
  "rich>=13.7",
  "typer>=0.12"
]
```

- [ ] **Step 2: Refresh the lock file**

Run:

```bash
uv lock
```

Expected: the editable `magicmd` package lists Playwright as a direct dependency, `package.metadata.requires-dist` contains `>=1.60,<1.61`, and the resolved Playwright version remains 1.60.0.

- [ ] **Step 3: Run the metadata test and verify green**

Run:

```bash
uv run pytest tests/test_project_metadata.py::test_project_metadata_constrains_playwright_for_camoufox -q
```

Expected: PASS.

- [ ] **Step 4: Run the real browser smoke test with the locked dependency**

Run:

```bash
MAGICMD_RUN_BROWSER_SMOKE=1 uv run pytest \
  tests/test_browser_fetcher.py::test_camoufox_can_create_page -q
```

Expected: PASS without making any network request.

- [ ] **Step 5: Inspect the lock-file compatibility boundary**

Run:

```bash
uv tree --package magicmd | rg 'camoufox|playwright'
```

Expected: Camoufox 0.4.11 and Playwright 1.60.0; no Playwright 1.61.x package.

- [ ] **Step 6: Commit the dependency fix**

```bash
git add pyproject.toml uv.lock
git commit -m "fix: 约束 Camoufox 的 Playwright 兼容版本"
```

### Task 3: Prepare the v0.7.1 patch release metadata

**Files:**

- Modify: `pyproject.toml`
- Modify: `src/magicmd/__init__.py`
- Modify: `npm/magicmd/package.json`
- Modify: `uv.lock`
- Modify: `CHANGELOG.md`
- Create: `docs/releases/v0.7.1.md`
- Test: `tests/test_project_metadata.py`

- [ ] **Step 1: Synchronize package versions to 0.7.1**

Apply these exact values:

```toml
# pyproject.toml
version = "0.7.1"
```

```python
# src/magicmd/__init__.py
__version__ = "0.7.1"
```

```json
// npm/magicmd/package.json
"version": "0.7.1"
```

- [ ] **Step 2: Refresh the lock file after the version change**

Run:

```bash
uv lock
```

Expected: the editable `magicmd` package in `uv.lock` is version 0.7.1 and retains the direct Playwright constraint.

- [ ] **Step 3: Replace the empty Unreleased changelog entries**

Set the top of `CHANGELOG.md` to:

```markdown
## Unreleased

### 中文

- 修复 npm wrapper 和 `uvx --from magicmd` 可能解析到不兼容 Playwright 版本的问题；发布元数据现在将 Camoufox 0.4.11 约束在已验证的 Playwright 1.60 兼容区间。
- 新增真实 Camoufox `Browser.new_page()` 冒烟测试入口，用于发布前验证浏览器协议兼容性。

### English

- Fixed npm wrapper and `uvx --from magicmd` installs resolving an incompatible Playwright version; published metadata now keeps Camoufox 0.4.11 on the verified Playwright 1.60 compatibility range.
- Added an opt-in real Camoufox `Browser.new_page()` smoke test for pre-release browser-protocol verification.
```

- [ ] **Step 4: Add the bilingual v0.7.1 release note**

Create `docs/releases/v0.7.1.md` with:

````markdown
# MagicMD v0.7.1

v0.7.1 修复 npm wrapper 和 `uvx --from magicmd` 安装路径中的浏览器依赖兼容问题。

MagicMD 使用 Camoufox 抓取微信公众号等需要浏览器渲染的页面。Playwright 1.61.0 创建页面时发送的新 viewport 字段无法被当前稳定版 Camoufox 浏览器协议识别，导致抓取在访问文章之前失败。本版本在发布元数据中加入 `playwright>=1.60,<1.61`，确保隔离安装和 npm wrapper 默认使用已验证可用的 Playwright 1.60。

## 修复与验证

- 约束 Playwright 到 Camoufox 0.4.11 已验证兼容的 1.60 版本线。
- 新增发布元数据回归测试，防止兼容约束意外丢失。
- 新增可选真实浏览器冒烟测试，在不访问外部网站的情况下验证 `Browser.new_page()`。

## 升级

```bash
uv tool install --upgrade magicmd
# 或
pipx upgrade magicmd
# npm wrapper
npm install -g magicmd@0.7.1
```
````

---

# MagicMD v0.7.1

v0.7.1 fixes browser dependency compatibility for npm wrapper and `uvx --from magicmd` installations.

MagicMD uses Camoufox for sites that require browser rendering, including WeChat Official Account articles. Playwright 1.61.0 sends a new viewport field that the current stable Camoufox browser protocol does not recognize, so page creation fails before the article is visited. This release adds `playwright>=1.60,<1.61` to published metadata so isolated installations and the npm wrapper use the verified Playwright 1.60 line.

## Fixes and Verification

- Constrained Playwright to the 1.60 line verified with Camoufox 0.4.11.
- Added a published-metadata regression test that protects the compatibility range.
- Added an opt-in real-browser smoke test for `Browser.new_page()` without external network access.

## Upgrade

```bash
uv tool install --upgrade magicmd
# or
pipx upgrade magicmd
# npm wrapper
npm install -g magicmd@0.7.1
```

````

- [ ] **Step 5: Run version and metadata tests**

Run:

```bash
uv run pytest tests/test_project_metadata.py tests/test_cli.py -q
````

Expected: PASS, including npm/Python version parity and CLI version output.

- [ ] **Step 6: Commit the release preparation**

```bash
git add pyproject.toml src/magicmd/__init__.py npm/magicmd/package.json \
  uv.lock CHANGELOG.md docs/releases/v0.7.1.md
git commit -m "chore: 准备 v0.7.1 兼容性修复版本"
```

### Task 4: Verify source, built artifacts, and isolated resolution

**Files:**

- Verify: all changed files
- Build output: `dist/magicmd-0.7.1-py3-none-any.whl`

- [ ] **Step 1: Run the complete Python test suite**

Run:

```bash
uv run pytest -q
```

Expected: all default tests pass; the real-browser smoke test is skipped unless explicitly enabled.

- [ ] **Step 2: Run the real browser smoke test explicitly**

Run:

```bash
MAGICMD_RUN_BROWSER_SMOKE=1 uv run pytest \
  tests/test_browser_fetcher.py::test_camoufox_can_create_page -q
```

Expected: PASS.

- [ ] **Step 3: Run static checks**

Run:

```bash
uv run ruff check .
```

Expected: `All checks passed!`.

- [ ] **Step 4: Build and validate release artifacts**

Run:

```bash
rm -rf dist
uv build
uv run --with twine twine check dist/*
npm pack --dry-run --prefix npm/magicmd
```

Expected: wheel and source distribution build successfully, Twine reports both distributions as PASSED, and npm dry-run reports package version 0.7.1 without publishing.

- [ ] **Step 5: Verify isolated wheel resolution**

Run:

```bash
uv run --isolated --no-project \
  --with ./dist/magicmd-0.7.1-py3-none-any.whl \
  python -c 'import importlib.metadata as m; print(m.version("magicmd"), m.version("camoufox"), m.version("playwright"))'
```

Expected: `0.7.1 0.4.11 1.60.0` or another Playwright 1.60.x patch version, never 1.61.x.

- [ ] **Step 6: Verify the built wheel at the real protocol boundary**

Run:

```bash
uv run --isolated --no-project \
  --with ./dist/magicmd-0.7.1-py3-none-any.whl \
  python - <<'PY'
import asyncio

from camoufox.async_api import AsyncCamoufox


async def main():
    async with AsyncCamoufox(headless=True) as browser:
        await browser.new_page()
    print("new_page: OK")


asyncio.run(main())
PY
```

Expected: `new_page: OK`.

- [ ] **Step 7: Review the final diff and repository state**

Run:

```bash
git diff HEAD~3 --check
git status --short
git log --oneline -4
```

Expected: no whitespace errors; only intentional build artifacts may be untracked, and the three implementation commits are visible after the design commit.

Do not publish packages, create a Git tag, push commits, or trigger the publish workflow in this task.
