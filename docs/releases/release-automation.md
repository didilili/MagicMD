# Release Automation Plan

这份文档记录 MagicMD 后续发布自动化方案。目标不是马上把发布完全交给 CI，而是先把 PyPI、npm、GitHub Release 的权限模型和落地步骤讲清楚，避免再次遇到手动 token、账号权限和目录位置问题。

## Recommendation

推荐分两步推进：

1. 短期继续手动发布，但严格使用 `docs/releases/post-release-checklist.md` 做 smoke test。
2. v0.5 期间新增一个 tag-triggered release workflow，并先通过 PyPI / npm Trusted Publishing 做无长期 token 发布。

不要在 trusted publisher 尚未配置完成前加入会自动 publish 的 workflow。否则下一次推 tag 时，CI 可能在 PyPI 或 npm 权限阶段失败，或者只发布了其中一个包，造成状态不一致。

## Current Manual Pain Points

v0.4.0 发布暴露了几个真实问题：

- PyPI 不再支持用户名/密码上传，必须使用 API token 或 Trusted Publisher。
- npm 的 `404 Not Found` 可能实际是未登录或没有 package owner 权限。
- npm wrapper 位于 `npm/magicmd/`，从仓库根目录和 wrapper 目录执行命令时，相对路径不同。
- GitHub Release 的 `--notes-file` 路径取决于当前工作目录，必要时要使用绝对路径。

这些都不是 MagicMD 包本身的问题，而是发布认证和操作入口不够固定。

## Trusted Publishing Sources

- PyPI Trusted Publisher: <https://docs.pypi.org/trusted-publishers/using-a-publisher/>
- npm Trusted Publishing: <https://docs.npmjs.com/trusted-publishers/>
- GitHub Actions OIDC permissions: <https://docs.github.com/actions/reference/openid-connect-reference>

Key points from the official docs:

- PyPI Trusted Publishing can use `pypa/gh-action-pypi-publish@release/v1` without username, password, or API token.
- GitHub Actions jobs that request OIDC tokens need `permissions: id-token: write`.
- npm Trusted Publishing also uses OIDC and requires a trusted publisher configuration on npmjs.com.
- npm Trusted Publishing requires Node `22.14.0` or newer and npm CLI `11.5.1` or newer.
- npm Trusted Publishing supports `npm publish` and `npm stage publish`; other stage approval commands still require interactive authentication.

## Proposed GitHub Environments

Create two GitHub environments:

- `pypi`
- `npm`

Recommended settings:

- Require manual approval for both environments until the workflow has shipped at least one clean release.
- Restrict deployments to protected tags matching `v*`.
- Keep `contents: read` and `id-token: write` scoped to publish jobs, not the whole workflow.

## PyPI Setup

In the PyPI project settings for `magicmd`, add a trusted publisher:

- Publisher: GitHub Actions
- Owner: `didilili`
- Repository: `MagicMD`
- Workflow filename: `publish.yml`
- Environment: `pypi`

After this is configured, the workflow can publish with:

```yaml
- name: Publish Python package to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
```

No `PYPI_TOKEN`, username, or password should be needed.

## npm Setup

In the npm package settings for `magicmd`, add a trusted publisher:

- Publisher: GitHub Actions
- Organization or user: `didilili`
- Repository: `MagicMD`
- Workflow filename: `publish.yml`
- Environment name: `npm`
- Allowed actions: `npm publish`

The npm package already exists, so the initial manual publish limitation is no longer relevant. The workflow should publish from `npm/magicmd/`:

```bash
npm publish --registry=https://registry.npmjs.org/
```

Do not rely on `npm whoami` in the workflow. With OIDC, `npm whoami` does not reflect trusted publishing authentication status; the auth exchange happens during `npm publish`.

## Proposed Workflow Shape

Create `.github/workflows/publish.yml` only after PyPI and npm trusted publishers are configured.

```yaml
name: Publish Release

on:
  push:
    tags:
      - "v*"
  workflow_dispatch:
    inputs:
      version:
        description: "Version to publish, for example 0.5.0"
        required: true

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.11

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run tests
        run: uv run pytest -q

      - name: Run ruff
        run: uv run ruff check .

      - name: Build Python package
        run: uv build

      - name: Check Python distributions
        run: uvx twine check dist/*

  publish-pypi:
    needs: verify
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Set up Python
        run: uv python install 3.11

      - name: Build Python package
        run: uv build

      - name: Publish Python package to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

  publish-npm:
    needs: publish-pypi
    runs-on: ubuntu-latest
    environment: npm
    permissions:
      contents: read
      id-token: write
    defaults:
      run:
        working-directory: npm/magicmd
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: 24
          registry-url: https://registry.npmjs.org/
          cache: npm
          cache-dependency-path: package-lock.json

      - name: Ensure npm supports trusted publishing
        run: npm install -g npm@latest

      - name: Dry run npm package
        run: npm pack --dry-run

      - name: Publish npm package
        run: npm publish --registry=https://registry.npmjs.org/
```

## Open Decisions Before Implementation

- Whether to create GitHub Release in the same workflow or keep it manual. Current recommendation: keep GitHub Release manual until PyPI/npm automation succeeds once.
- Whether npm should use `npm publish` or `npm stage publish`. Current recommendation: start with `npm publish`; consider staged publishing after the process is stable.
- Whether to allow `workflow_dispatch`. Current recommendation: keep it only if maintainers want emergency reruns, and require environment approval.
- Whether to publish npm if PyPI fails. Current recommendation: npm should depend on PyPI because the npm wrapper executes the PyPI CLI through `uvx`.

## Safer Manual Flow Until Automation Lands

Use this flow for the next release if the trusted publishers are not configured yet:

```bash
VERSION=0.5.0
TAG="v${VERSION}"

uv run ruff check .
uv run python -m pytest -q
rm -f dist/*.whl dist/*.tar.gz
uv build
uvx twine check dist/*

git tag -a "$TAG" -m "MagicMD ${TAG}"
git push origin main
git push origin "$TAG"

uv publish --username __token__ --password "$PYPI_TOKEN"

cd npm/magicmd
npm publish --registry=https://registry.npmjs.org/
cd ../..

gh release create "$TAG" \
  --title "MagicMD ${TAG}" \
  --notes-file "docs/releases/${TAG}.md"

VERSION="$VERSION" bash -c '
python3 -m pip index versions magicmd
uvx --from "magicmd==${VERSION}" magicmd --version
npm view magicmd version --registry=https://registry.npmjs.org/
npx "magicmd@${VERSION}" --version
'
```

For PyPI token publishing, set `PYPI_TOKEN` in the shell for the current session and unset it after publishing:

```bash
export PYPI_TOKEN="pypi-..."
uv publish --username __token__ --password "$PYPI_TOKEN"
unset PYPI_TOKEN
```

## Failure Recovery Notes

- If PyPI fails before uploading any file, fix auth and rerun `uv publish`.
- If PyPI publishes but npm fails, keep the same version and retry npm after fixing npm owner/login/trusted publisher settings.
- If npm says `404 Not Found` during publish, check `npm whoami` locally and confirm the account is an owner of `magicmd`.
- If GitHub Release creation says `Release.tag_name already exists`, the release probably already exists; confirm with `gh release view "$TAG"`.
