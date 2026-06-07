---
title: 故障排查
description: 安装、采集、媒体下载和批量转换中常见问题的处理方式。
---

# 故障排查

遇到问题时，先运行：

```bash
magicmd doctor
```

它会检查当前环境里 MagicMD、Python、浏览器相关依赖和外部命令是否可用。

## 命令找不到

如果你还没有全局安装，把命令换成：

```bash
uv run magicmd --version
```

全局安装推荐：

```bash
uv tool install magicmd
```

如果是 npm 安装，确认本机能使用 `uvx`：

```bash
uvx --version
magicmd doctor
```

## 微信视频打不开或下载失败

微信视频经常带签名、Referer 或临时权限。MagicMD 会尽量提取链接并下载；如果下载失败，报告里会保留失败原因。对于 403 或签名过期的链接，通常需要回到原文环境中人工复核。

## 图片缺失

先检查文章目录里的 `images/`，再看 `extraction-report.json`。常见原因包括：

- 原文图片防盗链。
- 网络中断。
- 图片是动态修饰素材，被 MagicMD 过滤。
- 原文使用懒加载或非常规属性。

## 代码块内容不对

先升级 MagicMD，再重新跑一次：

```bash
uv tool upgrade magicmd
magicmd "ARTICLE_URL" -o output/
```

如果仍然不对，请保留原文链接、`article.md` 和 `extraction-report.json`，这三样最有助于定位平台规则。

## 批量任务中断

重新运行并跳过已存在结果：

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

如果你想完全重跑某篇文章，删除对应输出目录后再运行。
