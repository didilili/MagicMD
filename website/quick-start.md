---
title: 快速开始
description: 安装 MagicMD，并把第一篇公开文章转换成 Markdown 内容包。
---

# 快速开始

MagicMD 的使用方式很直接：给它一条公开文章链接，它会在 `output/` 下生成一份可保存、可发布、可复核的内容包。

## 安装

推荐用 `uv` 安装：

```bash
uv tool install magicmd
magicmd doctor
```

如果你习惯 `pipx`：

```bash
pipx install magicmd
magicmd doctor
```

npm 包是一个轻量入口，底层会调用 PyPI 版 MagicMD CLI：

```bash
npm install -g magicmd
magicmd doctor
```

## 转换单篇文章

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

指定输出目录：

```bash
magicmd convert "https://juejin.cn/post/example" -o output/
```

## 批量转换

准备 `urls.txt`：

```text
https://mp.weixin.qq.com/s/example
https://juejin.cn/post/example
https://blog.csdn.net/user/article/details/123
```

运行：

```bash
magicmd batch urls.txt -o output/
```

断点续跑时可以跳过已经存在的内容包：

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

## 输出结构

```text
output/article-title/
├── article.md
├── metadata.json
├── extraction-report.json
└── images/
    ├── img_001.png
    └── img_002.png
```

`article.md` 是正文，`metadata.json` 是文章元信息，`extraction-report.json` 是转换报告。批量任务还会生成 batch 报告，方便你快速检查失败原因和 warning。

## 使用配置

复制项目里的示例配置：

```bash
cp .magicmd.example.toml .magicmd.toml
magicmd "https://mp.weixin.qq.com/s/example" --config .magicmd.toml
```

也可以直接用 [配置生成器](/config-builder) 生成一份适合你网站的 `.magicmd.toml`。
