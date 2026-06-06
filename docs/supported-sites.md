# 支持站点 / Supported Sites

这份文档记录 MagicMD v0.1 对不同站点的真实支持状态。它不是营销清单，而是当前代码、配置和真实转换验证共同形成的基线。

This document records the real MagicMD v0.1 support status for each site. It is a validation baseline, not a marketing list.

## 当前支持矩阵

| 站点 | 状态 | 默认抓取模式 | 说明 |
| --- | --- | --- | --- |
| 微信公众号 `mp.weixin.qq.com` | 稳定主目标 | `camoufox` | v0.1 的主要验证对象，已有真实样本回归清单和多轮格式修复。 |
| CSDN `blog.csdn.net` | 实验支持 | `camoufox` | 真实样本可转换正文；普通 HTTP 在验证中返回 521，因此默认使用浏览器模式。仍需继续优化代码块和站内组件清理。 |
| 掘金 `juejin.cn` | 实验支持 | `camoufox` | 首页 5 篇真实样本已通过默认配置转换；普通 HTTP 抓取会偶发拿到字节 WAF challenge，因此默认使用浏览器模式。 |
| 通用网页 | 尽力支持 | `http` | 对带有标准 `article`、`main` 或 Open Graph 元信息的公开静态页面做基础提取。 |

## English Matrix

| Site | Status | Default fetch mode | Notes |
| --- | --- | --- | --- |
| WeChat Official Account `mp.weixin.qq.com` | Stable primary target | `camoufox` | Main v0.1 validation target with a live regression corpus and multiple formatting fixes. |
| CSDN `blog.csdn.net` | Experimental support | `camoufox` | Live samples converted with article body content. Plain HTTP returned 521 during validation, so browser mode is the default. Code block and site-widget cleanup still need more samples. |
| Juejin `juejin.cn` | Experimental support | `camoufox` | Five live homepage samples converted with the default configuration. Plain HTTP can intermittently return a ByteDance WAF challenge, so browser mode is the default. |
| Generic pages | Best effort | `http` | Basic extraction for public static pages with standard `article`, `main`, or Open Graph metadata. |

## 验证命令

可以用下面的方式继续扩大 CSDN/掘金样本：

```bash
uv run magicmd batch urls.txt -o output/site-validation-next --no-images
```

如果要显式让 CSDN 或其他站点走浏览器模式，可以在 `.magicmd.toml` 中配置：

```toml
[platforms.csdn]
enabled = true
browser = "camoufox"
wait_selector = "#content_views"
```

## 边界

MagicMD 只处理公开文章页面。登录、付费墙、验证码、私有内容、平台风控挑战、App-only 页面都不属于 v0.1 的支持范围。对于受平台访问限制的页面，MagicMD 应该记录失败或 warning，而不是绕过访问控制。

MagicMD only targets public article pages. Login-only content, paywalls, CAPTCHA, private pages, platform access challenges, and app-only pages are outside the v0.1 scope. When access is restricted, MagicMD should report a failure or warning instead of bypassing access controls.
