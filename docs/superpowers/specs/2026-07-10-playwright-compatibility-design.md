# Playwright 兼容性约束设计

## 背景

MagicMD 通过 Camoufox 启动浏览器抓取微信公众号等需要浏览器渲染的页面。当前发布元数据只直接声明 `camoufox[geoip]>=0.4`，而 Camoufox 0.4.11 对 Playwright 没有上限约束。未指定版本的 `uvx --from magicmd` 首次解析到某个 MagicMD 版本后可能继续复用缓存；即使重新安装 npm wrapper，也不保证 Python 包同步升级。与此同时，重新解析依赖时可能组合出 Camoufox 0.4.11、Camoufox 浏览器 v135.0.1-beta.24 和 Playwright 1.61.0。

Playwright 1.61.0 创建默认页面时向 `Browser.setDefaultViewport` 发送 `viewport.isMobile=false`，Camoufox 当前浏览器协议不认识该字段，导致 `browser.new_page()` 在访问文章 URL 之前失败。相同环境仅把 Playwright 改为 1.60.0 后可以成功创建页面。

## 目标

- 让 PyPI 安装、`uvx --from magicmd` 和 npm wrapper 默认解析到已验证兼容的 Playwright 版本。
- 让 npm wrapper 从自身 `package.json` 读取版本，并通过 `uvx --from "magicmd==<npm version>"` 请求同版本 Python 包。
- 让 Windows npm wrapper 直接启动 setup-uv 提供的 `uvx.exe`，不依赖不可直接执行的 `.cmd` launcher，也不启用 shell。
- 在发布 npm wrapper 前，验证同版本 Python 包已在 PyPI 可解析；同时发布两个包时等待 PyPI，同版本 npm-only 仅作为 PyPI 已成功后的恢复路径。
- 用快速、确定性的测试保护发布元数据中的兼容区间。
- 提供不导航到外部网站的真实浏览器冒烟测试，验证 Playwright 与 Camoufox 协议可以完成 `new_page()`；首次启动仍可能下载 Camoufox 运行时资源。
- 准备 v0.7.1 补丁版本所需的版本号和发行说明，但不在本任务中发布、打标签或推送远端。

## 非目标

- 不修改微信公众号解析器、抓取重试或 viewport 参数来掩盖协议错误。
- 不切换浏览器实现，也不在没有兼容性证据时升级 Camoufox。
- 不让默认单元测试依赖本机已下载 Camoufox 浏览器。

## 方案选择

采用直接依赖约束 `playwright>=1.60,<1.61`。相比固定 `==1.60.0`，兼容区间允许未来 1.60 补丁版本；相比只约束 Camoufox，直接约束 Playwright 能控制实际触发协议错误的解析结果。等上游 Camoufox 浏览器明确支持 1.61 或更高版本后，再通过独立兼容性验证放宽上限。

## 修改范围

1. 在 `pyproject.toml` 的运行时依赖中加入 `playwright>=1.60,<1.61`，并更新 `uv.lock`。
2. 在 `tests/test_project_metadata.py` 中解析项目依赖，断言发布元数据保留该兼容区间；在 POSIX 上用真实 Node wrapper 和临时 fake `uvx` 断言实际 argv 把 `magicmd==<npm version>` 放在 `--from` 后，并在 npm README 中记录相同版本命令。实际 argv 测试通过临时改回未固定版本的 mutation 验证红灯，再恢复实现转绿；Windows 由真实 CI smoke 覆盖，不再伪造 `uvx.cmd`。
3. 在 `npm/magicmd/bin/magicmd.js` 中将 npm 版本绑定到同版本 Python 包，Windows 选择 `uvx.exe`、其他平台选择 `uvx`，保持 `spawnSync` 默认 shell 关闭；同步更新 `npm/magicmd/README.md`。
4. 在 `.github/workflows/ci.yml` 新增 `windows-latest` npm wrapper smoke job：setup-uv 安装真实 `uvx.exe`，CI checkout 中仅把 `npm/magicmd/package.json` 改为已发布的 0.7.0，再运行 Node wrapper 并验证 `MagicMD 0.7.0`，避免发布前依赖 0.7.1。
5. 在 `.github/workflows/publish.yml` 的 `publish-npm` job 中安装 uv，并以有界重试运行 `uvx --refresh-package magicmd --from "magicmd==${MAGICMD_VERSION}" magicmd --version`；精确版本在 PyPI 不可用时，npm dry run 和发布都不得开始。同步更新 `docs/releases/release-automation.md`。
6. 在 `tests/test_browser_fetcher.py` 中加入真实 Camoufox 冒烟测试。测试默认跳过；仅当 `MAGICMD_RUN_BROWSER_SMOKE=1` 时启动浏览器并执行 `browser.new_page()`，不导航到外部网站。显式启用后，浏览器未安装或协议不兼容都应让测试失败，而不是静默跳过。
7. 将 Python 包、Python `__version__`、npm wrapper 和锁文件版本更新为 0.7.1，并增加中英文 v0.7.1 发行说明；同步把根 README、Agent Skill、排障、开发和网站示例中的精确 `uvx` 命令固定到 `magicmd==0.7.1`。

## 测试与验收

- 红灯：新增元数据测试在实现前失败，明确指出缺少 `playwright>=1.60,<1.61`。
- 红灯：npm wrapper 实际 argv 测试在 unversioned mutation 下失败，明确显示 `--from` 收到 `magicmd` 而不是同版本 Python 包 spec。
- 红灯：平台 launcher 和 CI 结构测试明确指出 Windows 仍使用 `uvx.cmd` 且缺少真实 `uvx.exe` smoke job。
- 红灯：npm 发布 workflow 测试在实现前失败，明确指出 `publish-npm` 缺少 setup-uv 和精确 PyPI 版本 guard。
- 绿灯：元数据测试、浏览器抓取单测和完整测试套件通过。
- 真实冒烟：`MAGICMD_RUN_BROWSER_SMOKE=1 uv run pytest tests/test_browser_fetcher.py -q` 能创建并关闭页面。
- 解析验证：在隔离环境中安装当前项目，确认 Playwright 解析为 1.60.x，并运行 `magicmd --version`。
- 静态检查：`uv run ruff check .` 通过。

## 风险与回滚

- 风险是 Playwright 1.60.x 未来无法满足其他依赖；当前 Camoufox 0.4.11 没有更高的 Playwright 下限，现有锁文件也已使用 1.60.0，因此风险较低。
- PyPI 简单索引传播可能晚于 Trusted Publishing job 完成；npm job 使用 12 次、每次间隔 10 秒的有界重试，超时后明确失败，避免发布一个暂时无法解析同版本 Python 包的 npm wrapper。
- 如果上游发布兼容版本，可先在隔离环境运行真实冒烟测试，再放宽 Playwright 上限并发布新的补丁版本。
- 如果约束造成意外解析冲突，回滚 v0.7.1 的依赖与版本元数据即可；不涉及内容格式或数据迁移。
