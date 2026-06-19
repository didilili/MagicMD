# Post-release Checklist

这份清单用于每次发布后验证真实用户是否能安装和运行最新版本。它不替代 CI；它检查的是 PyPI、npm、GitHub Release 和 Skill 安装路径是否已经真正对外可用。

## 1. Confirm GitHub Release

```bash
VERSION=0.5.0
TAG="v${VERSION}"

gh release view "$TAG" --repo didilili/MagicMD --json tagName,name,url,isDraft,isPrerelease,publishedAt
```

Expected:

- `tagName` is the release tag, for example `v${VERSION}`.
- `isDraft` is `false`.
- `isPrerelease` is `false` for stable releases.
- `url` opens the public release page.

## 2. Confirm Publish Workflow

If the release used `.github/workflows/publish.yml`, confirm the run completed:

```bash
gh run list \
  --repo didilili/MagicMD \
  --workflow publish.yml \
  --limit 5
```

Expected:

- The release run completed successfully.
- PyPI publishing used the `pypi` environment when `publish_pypi` was checked.
- npm publishing used the `npm` environment when `publish_npm` was checked.

## 3. Confirm PyPI

```bash
python3 -m pip index versions magicmd
uvx --from "magicmd==${VERSION}" magicmd --version
```

Expected:

- The latest version appears in the PyPI version list.
- `uvx` prints `MagicMD ${VERSION}`.

## 4. Confirm npm

```bash
npm view magicmd version --registry=https://registry.npmjs.org/
npx "magicmd@${VERSION}" --version
```

Expected:

- `npm view` prints the latest version.
- `npx` prints `MagicMD ${VERSION}`.

## 5. Confirm Docs

Open:

- `https://magicmd.cn/`
- `https://github.com/didilili/MagicMD/releases/tag/v${VERSION}`

Expected:

- The website deploy is current.
- The release notes match `docs/releases/v${VERSION}.md`.
- Install commands point to the released version through PyPI or npm.

## 6. Confirm Agent Skill Path

Ask a Skill-capable agent:

```text
请从 GitHub 仓库 didilili/MagicMD 安装 MagicMD Skill，Skill 路径是 skills/magicmd。
```

Expected:

- The agent can locate `skills/magicmd`.
- The Skill instructions call the MagicMD CLI instead of duplicating conversion logic.
- The install path works for a fresh user-facing setup.

## 7. Record Release Notes

After all checks pass, update the next release prep notes with:

- Release tag.
- PyPI version.
- npm version.
- Smoke test date.
- Any manual publishing or authentication issue encountered.

If publishing exposed authentication or workflow issues, update `docs/releases/release-automation.md` while the details are still fresh.
