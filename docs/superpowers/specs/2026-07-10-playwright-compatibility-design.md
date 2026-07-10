# Playwright 兼容性约束设计

## 背景

MagicMD 通过 Camoufox 启动浏览器抓取微信公众号等需要浏览器渲染的页面。当前发布元数据只直接声明 `camoufox[geoip]>=0.4`，而 Camoufox 0.4.11 对 Playwright 没有上限约束。npm wrapper 每次执行 `uvx --from magicmd` 时会重新解析依赖，因此在 Playwright 1.61.0 发布后，最终组合变成 Camoufox 0.4.11、Camoufox 浏览器 v135.0.1-beta.24 和 Playwright 1.61.0。

Playwright 1.61.0 创建默认页面时向 `Browser.setDefaultViewport` 发送 `viewport.isMobile=false`，Camoufox 当前浏览器协议不认识该字段，导致 `browser.new_page()` 在访问文章 URL 之前失败。相同环境仅把 Playwright 改为 1.60.0 后可以成功创建页面。

## 目标

- 让 PyPI 安装、`uvx --from magicmd` 和 npm wrapper 默认解析到已验证兼容的 Playwright 版本。
- 用快速、确定性的测试保护发布元数据中的兼容区间。
- 提供不访问外部网站的真实浏览器冒烟测试，验证 Playwright 与 Camoufox 协议可以完成 `new_page()`。
- 准备 v0.7.1 补丁版本所需的版本号和发行说明，但不在本任务中发布、打标签或推送远端。

## 非目标

- 不修改微信公众号解析器、抓取重试或 viewport 参数来掩盖协议错误。
- 不切换浏览器实现，也不在没有兼容性证据时升级 Camoufox。
- 不让默认单元测试依赖本机已下载 Camoufox 浏览器。

## 方案选择

采用直接依赖约束 `playwright>=1.60,<1.61`。相比固定 `==1.60.0`，兼容区间允许未来 1.60 补丁版本；相比只约束 Camoufox，直接约束 Playwright 能控制实际触发协议错误的解析结果。等上游 Camoufox 浏览器明确支持 1.61 或更高版本后，再通过独立兼容性验证放宽上限。

## 修改范围

1. 在 `pyproject.toml` 的运行时依赖中加入 `playwright>=1.60,<1.61`，并更新 `uv.lock`。
2. 在 `tests/test_project_metadata.py` 中解析项目依赖，断言发布元数据保留该兼容区间。该测试先以缺少直接依赖为原因失败，再由元数据修改转绿。
3. 在 `tests/test_browser_fetcher.py` 中加入真实 Camoufox 冒烟测试。测试默认跳过；仅当 `MAGICMD_RUN_BROWSER_SMOKE=1` 时启动浏览器并执行 `browser.new_page()`，不访问网络。显式启用后，浏览器未安装或协议不兼容都应让测试失败，而不是静默跳过。
4. 将 Python 包、Python `__version__`、npm wrapper 和锁文件版本更新为 0.7.1，并增加中英文 v0.7.1 发行说明。

## 测试与验收

- 红灯：新增元数据测试在实现前失败，明确指出缺少 `playwright>=1.60,<1.61`。
- 绿灯：元数据测试、浏览器抓取单测和完整测试套件通过。
- 真实冒烟：`MAGICMD_RUN_BROWSER_SMOKE=1 uv run pytest tests/test_browser_fetcher.py -q` 能创建并关闭页面。
- 解析验证：在隔离环境中安装当前项目，确认 Playwright 解析为 1.60.x，并运行 `magicmd --version`。
- 静态检查：`uv run ruff check .` 通过。

## 风险与回滚

- 风险是 Playwright 1.60.x 未来无法满足其他依赖；当前 Camoufox 0.4.11 没有更高的 Playwright 下限，现有锁文件也已使用 1.60.0，因此风险较低。
- 如果上游发布兼容版本，可先在隔离环境运行真实冒烟测试，再放宽 Playwright 上限并发布新的补丁版本。
- 如果约束造成意外解析冲突，回滚 v0.7.1 的依赖与版本元数据即可；不涉及内容格式或数据迁移。
