# Playwright Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a release-ready MagicMD v0.7.1 whose published dependency metadata constrains Playwright to the 1.60 line verified with Camoufox 0.4.11, whose npm wrapper requests the same-version Python package through the correct platform executable, whose npm publish job waits for that exact Python version on PyPI, and whose tests expose future browser-protocol regressions.

**Architecture:** Add a direct Playwright compatibility constraint at the package boundary because `uvx --from magicmd` resolves from published metadata rather than this repository's lock file. Since an unversioned `uvx` invocation can reuse a previously cached MagicMD version, bind the npm wrapper version to `magicmd==<npm version>`. On POSIX, verify actual argv with a fake executable; on Windows, select `uvx.exe` without a shell and exercise it on `windows-latest` using published MagicMD 0.7.0 so pre-release CI does not require 0.7.1. Before npm publishing, use a bounded retry guard to require the exact Python version from PyPI, covering both combined publishing and npm-only recovery. Add an opt-in Camoufox smoke test that exercises the real `Browser.new_page()` protocol boundary without navigating to an external website; first startup may still download runtime assets. Prepare synchronized Python/npm version metadata and release notes without publishing, tagging, pushing, or changing fetch/parse behavior.

**Tech Stack:** Python 3.11+, Hatch/PEP 621 metadata, uv, pytest/pytest-asyncio, Camoufox, Playwright, npm wrapper

---

### Task 1: Add failing compatibility regression tests

**Files:**

- Modify: `tests/test_project_metadata.py`
- Modify: `tests/test_browser_fetcher.py`

- [x] **Step 1: Add the publishing-metadata regression test**

Append this test near the existing project metadata tests:

```python
def test_project_metadata_constrains_playwright_for_camoufox():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert "playwright>=1.60,<1.61" in metadata["project"]["dependencies"]
```

- [x] **Step 2: Run the metadata test and verify the expected red state**

Run:

```bash
uv run pytest tests/test_project_metadata.py::test_project_metadata_constrains_playwright_for_camoufox -q
```

Expected: FAIL because `pyproject.toml` does not yet directly declare `playwright>=1.60,<1.61`.

- [x] **Step 3: Add the opt-in real-browser smoke test**

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

- [x] **Step 4: Run the smoke test against the known-bad dependency and verify red**

Before changing `pyproject.toml`, run:

```bash
MAGICMD_RUN_BROWSER_SMOKE=1 uv run --isolated --no-project \
  --with '.[dev]' \
  --with 'playwright==1.61.0' \
  pytest tests/test_browser_fetcher.py::test_camoufox_can_create_page -q
```

Expected: FAIL at `Browser.new_page()` with `Browser.setDefaultViewport` rejecting `viewport.isMobile`.

- [x] **Step 5: Confirm the normal test suite still skips the opt-in smoke test**

Run:

```bash
uv run pytest tests/test_browser_fetcher.py -q
```

Expected: `2 passed, 1 skipped`.

- [x] **Step 6: Commit the regression tests**

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

- [x] **Step 1: Add the minimal direct dependency constraint**

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

- [x] **Step 2: Refresh the lock file**

Run:

```bash
uv lock
```

Expected: the editable `magicmd` package lists Playwright as a direct dependency, `package.metadata.requires-dist` contains `>=1.60,<1.61`, and the resolved Playwright version remains 1.60.0.

- [x] **Step 3: Run the metadata test and verify green**

Run:

```bash
uv run pytest tests/test_project_metadata.py::test_project_metadata_constrains_playwright_for_camoufox -q
```

Expected: PASS.

- [x] **Step 4: Run the real browser smoke test with the locked dependency**

Run:

```bash
MAGICMD_RUN_BROWSER_SMOKE=1 uv run pytest \
  tests/test_browser_fetcher.py::test_camoufox_can_create_page -q
```

Expected: PASS without navigating to an external website. First Camoufox startup may still download runtime assets.

- [x] **Step 5: Inspect the lock-file compatibility boundary**

Run:

```bash
uv tree --package magicmd | rg 'camoufox|playwright'
```

Expected: Camoufox 0.4.11 and Playwright 1.60.0; no Playwright 1.61.x package.

- [x] **Step 6: Commit the dependency fix**

```bash
git add pyproject.toml uv.lock
git commit -m "fix: 约束 Camoufox 的 Playwright 兼容版本"
```

### Task 3: Prepare the v0.7.1 patch release metadata

**Files:**

- Modify: `pyproject.toml`
- Modify: `src/magicmd/__init__.py`
- Modify: `npm/magicmd/package.json`
- Modify: `npm/magicmd/bin/magicmd.js`
- Modify: `npm/magicmd/README.md`
- Modify: `uv.lock`
- Modify: `CHANGELOG.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/publish.yml`
- Create: `docs/releases/v0.7.1.md`
- Modify: `docs/releases/release-automation.md`
- Modify: `docs/superpowers/specs/2026-07-10-playwright-compatibility-design.md`
- Modify: `docs/superpowers/plans/2026-07-10-playwright-compatibility.md`
- Modify: `SKILL.md`, `README.md`, `README_EN.md`, `skills/magicmd/SKILL.md`
- Modify: `docs/troubleshooting.md`, `docs/development.md`, `website/agent-skill.md`, `website/en/agent-skill.md`
- Test: `tests/test_project_metadata.py`

- [x] **Step 1: Synchronize package versions to 0.7.1**

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

- [x] **Step 2: Refresh the lock file after the version change**

Run:

```bash
uv lock
```

Expected: the editable `magicmd` package in `uv.lock` is version 0.7.1 and retains the direct Playwright constraint.

- [x] **Step 3: Add the npm-wrapper same-version regression test and verify red**

Keep metadata/README parity assertions, then add `test_npm_wrapper_forwards_same_version_python_package`. On POSIX, the test runs the real Node wrapper with a temporary fake `uvx`, captures its JSON argv, and requires `--from`, `magicmd==<npm version>`, `magicmd`, then the forwarded CLI arguments. Skip this fake-executable test on Windows because the dedicated CI job exercises the real `uvx.exe`.

```bash
uv run pytest tests/test_project_metadata.py::test_npm_wrapper_forwards_same_version_python_package -q
```

Because the correct version-binding implementation already exists during review, temporarily mutate `pythonPackage` back to unversioned `magicmd` and verify RED at argv index 1, then restore the dynamic package spec and verify GREEN. Add separate RED assertions that require `uvx.exe` for `win32`, forbid `uvx.cmd` and `shell: true`, and require the Windows CI smoke job.

- [x] **Step 4: Bind the npm wrapper and use the correct platform launcher**

Read the version from `../package.json`, construct `pythonPackage`, and pass it after `--from` while preserving platform, signal, and exit handling:

```javascript
const { version: packageVersion } = require("../package.json");
const pythonPackage = `magicmd==${packageVersion}`;
const result = spawnSync(command, ["--from", pythonPackage, "magicmd", ...args], {
  stdio: "inherit"
});
```

Update the equivalent-command comment and missing-`uvx` error text to use `pythonPackage` rather than a hardcoded release version.

Select `uvx.exe` on Windows and `uvx` otherwise, without `shell: true`. Add `.github/workflows/ci.yml` job `npm-wrapper-windows` using `windows-latest`, setup-uv, and Node 24. In its checkout only, rewrite `npm/magicmd/package.json` to published version 0.7.0, run the real wrapper, and require `MagicMD 0.7.0`.

- [x] **Step 5: Document npm/Python version parity**

Update `npm/magicmd/README.md` to explain that `magicmd@0.7.1` requests `magicmd==0.7.1` and show:

```bash
uvx --from "magicmd==0.7.1" magicmd
```

Document that Windows launches `uvx.exe` directly while macOS/Linux launch `uvx`, with shell execution disabled. Sweep the user-facing README, Skill, troubleshooting, development, and website examples so exact commands use `uvx --from "magicmd==0.7.1" magicmd ...`.

- [x] **Step 6: Add the npm-publish PyPI guard test and verify red**

Parse only the `publish-npm` job in `.github/workflows/publish.yml` and require setup-uv plus a `Verify matching Python package is available on PyPI` step whose `MAGICMD_VERSION` comes from workflow input. Require the exact `uvx --refresh-package` command, bounded retry/sleep, and terminal failure message.

```bash
uv run pytest tests/test_project_metadata.py::test_publish_npm_waits_for_matching_python_package_on_pypi -q
```

Expected: FAIL because the npm job has no setup-uv or exact-version PyPI guard.

- [x] **Step 7: Guard npm publishing with the matching PyPI version**

In `publish-npm`, install `astral-sh/setup-uv@v5`, then run up to 12 attempts separated by 10 seconds:

```bash
uvx --refresh-package magicmd --from "magicmd==${MAGICMD_VERSION}" magicmd --version
```

The guard must run before npm pack/publish and fail clearly after the final attempt. Document in `docs/releases/release-automation.md` that npm-only is a recovery path only after the matching PyPI version is live.

- [x] **Step 8: Replace the empty Unreleased changelog entries**

Set the top of `CHANGELOG.md` to:

```markdown
## Unreleased

### 中文

- 修复 npm wrapper 和 `uvx --from magicmd` 可能解析到不兼容 Playwright 版本的问题；npm wrapper 现在固定请求同版本 Python 包，并在 Windows 上正确调用 `uvx.exe`，发布元数据将 Playwright 约束在与当前 Camoufox 0.4.11 已验证兼容的 1.60 版本线。
- 新增真实 Camoufox `Browser.new_page()` 冒烟测试入口，用于发布前验证浏览器协议兼容性。

### English

- Fixed npm wrapper and `uvx --from magicmd` installs resolving an incompatible Playwright version; the npm wrapper now requests the same-version Python package and correctly invokes `uvx.exe` on Windows, while published metadata constrains Playwright to the 1.60 line verified with current Camoufox 0.4.11.
- Added an opt-in real Camoufox `Browser.new_page()` smoke test for pre-release browser-protocol verification.
```

- [x] **Step 9: Add the bilingual v0.7.1 release note**

Create `docs/releases/v0.7.1.md` with:

````markdown
# MagicMD v0.7.1

v0.7.1 修复 npm wrapper 和 `uvx --from magicmd` 安装路径中的浏览器依赖兼容问题。

MagicMD 使用 Camoufox 抓取微信公众号等需要浏览器渲染的页面。Playwright 1.61.0 创建页面时发送的新 viewport 字段无法被当前稳定版 Camoufox 浏览器协议识别，导致抓取在访问文章之前失败。本版本在发布元数据中加入 `playwright>=1.60,<1.61`，确保隔离安装使用已验证可用的 Playwright 1.60；npm wrapper 还会读取自身版本并请求同版本 Python 包，避免复用 `uvx` 缓存中的旧版 MagicMD，并在 Windows 上直接调用由 `uv` 安装的 `uvx.exe`。

## 修复与验证

- 约束 Playwright 到 Camoufox 0.4.11 已验证兼容的 1.60 版本线。
- npm wrapper 固定请求 `magicmd==0.7.1`，确保 npm 与 Python 包版本一致；Windows 启动器直接使用 `uvx.exe`，不启用 shell。
- 新增发布元数据和 npm wrapper 回归测试，并增加 Windows CI 冒烟任务：它临时将 checkout 中的 npm 版本改为已发布的 0.7.0，再通过真实 `uvx.exe` 验证 wrapper，不依赖尚未发布的 0.7.1。
- 新增可选真实浏览器冒烟测试，在不导航到外部网站的情况下验证 `Browser.new_page()`；首次启动 Camoufox 仍可能下载运行时资源。

## 升级

```bash
uv tool install --upgrade magicmd
# 或
pipx upgrade magicmd
# npm wrapper
npm install -g magicmd@0.7.1
```

```bash
uvx --from "magicmd==0.7.1" magicmd --version
```

---

# MagicMD v0.7.1

v0.7.1 fixes browser dependency compatibility for npm wrapper and `uvx --from magicmd` installations.

MagicMD uses Camoufox for sites that require browser rendering, including WeChat Official Account articles. Playwright 1.61.0 sends a new viewport field that the current stable Camoufox browser protocol does not recognize, so page creation fails before the article is visited. This release adds `playwright>=1.60,<1.61` to published metadata so isolated installations use the verified Playwright 1.60 line. The npm wrapper also reads its own version and requests the same-version Python package, avoiding reuse of an older MagicMD version from the `uvx` cache, and directly invokes `uvx.exe`, which is installed with `uv`, on Windows.

## Fixes and Verification

- Constrained Playwright to the 1.60 line verified with Camoufox 0.4.11.
- Bound the npm wrapper to `magicmd==0.7.1` so the npm and Python package versions stay aligned; the Windows launcher uses `uvx.exe` directly without enabling a shell.
- Added published-metadata and npm-wrapper regression tests plus a Windows CI smoke job. The job changes only the checkout npm version to published 0.7.0, then verifies the wrapper through the real `uvx.exe` without depending on unpublished 0.7.1.
- Added an opt-in real-browser smoke test for `Browser.new_page()` without navigating to an external website; the first Camoufox startup may still download runtime assets.

## Upgrade

```bash
uv tool install --upgrade magicmd
# or
pipx upgrade magicmd
# npm wrapper
npm install -g magicmd@0.7.1
```

```bash
uvx --from "magicmd==0.7.1" magicmd --version
```
````

- [x] **Step 10: Run version and metadata tests**

Run:

```bash
uv run pytest tests/test_project_metadata.py tests/test_cli.py -q
```

Expected: PASS, including npm/Python version parity and CLI version output.

- [x] **Step 11: Amend the release preparation commit**

```bash
git add pyproject.toml src/magicmd/__init__.py npm/magicmd/package.json \
  npm/magicmd/bin/magicmd.js npm/magicmd/README.md uv.lock CHANGELOG.md \
  .github/workflows/ci.yml .github/workflows/publish.yml docs/releases/v0.7.1.md \
  docs/releases/release-automation.md \
  docs/superpowers/specs/2026-07-10-playwright-compatibility-design.md \
  docs/superpowers/plans/2026-07-10-playwright-compatibility.md tests/test_project_metadata.py
git commit --amend --no-edit
```

### Task 4: Verify source, built artifacts, and isolated resolution

**Files:**

- Verify: all changed files
- Build output: `dist/magicmd-0.7.1-py3-none-any.whl`

- [x] **Step 1: Run the complete Python test suite**

Run:

```bash
uv run pytest -q
```

Expected: all default tests pass; the real-browser smoke test is skipped unless explicitly enabled.

- [x] **Step 2: Run the real browser smoke test explicitly**

Run:

```bash
MAGICMD_RUN_BROWSER_SMOKE=1 uv run pytest \
  tests/test_browser_fetcher.py::test_camoufox_can_create_page -q
```

Expected: PASS.

- [x] **Step 3: Run static checks**

Run:

```bash
uv run ruff check .
```

Expected: `All checks passed!`.

- [x] **Step 4: Build and validate release artifacts**

Run:

```bash
rm -rf dist
uv build
uv run --with twine twine check dist/*
(cd npm/magicmd && npm pack --dry-run)
```

Expected: wheel and source distribution build successfully, Twine reports both distributions as PASSED, and npm dry-run reports package version 0.7.1 without publishing.

- [x] **Step 5: Verify isolated wheel resolution**

Run:

```bash
uv run --isolated --no-project \
  --with ./dist/magicmd-0.7.1-py3-none-any.whl \
  python -c 'import importlib.metadata as m; print(m.version("magicmd"), m.version("camoufox"), m.version("playwright"))'
```

Expected: `0.7.1 0.4.11 1.60.0` or another Playwright 1.60.x patch version, never 1.61.x.

- [x] **Step 6: Verify the built wheel at the real protocol boundary**

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

- [x] **Step 7: Review the final diff and repository state**

Run:

```bash
git diff HEAD~3 --check
git status --short
git log --oneline -4
```

Expected: no whitespace errors; only intentional build artifacts may be untracked, and the three implementation commits are visible after the design commit.

Do not publish packages, create a Git tag, push commits, or trigger the publish workflow in this task.
