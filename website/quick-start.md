---
title: 快速开始
description: 安装 MagicMD，并把第一篇公开文章转换成 Markdown 内容包。
---

# 快速开始

先照着这条最短路径跑一遍：安装 CLI，极速转换一篇公开文章，然后打开 `output/` 查看已经深度优化过的 Markdown 内容包。跑通之后，再开启批量转换和自定义输出规则。

## 1. 安装 MagicMD

推荐用 `uv` 安装，它会把命令行工具隔离到独立环境里：

```bash
uv tool install magicmd
magicmd doctor
```

`magicmd doctor` 用来检查本机环境和常见依赖。如果这一步通过，后面的转换命令就可以直接跑。

::: details 其他安装方式

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

:::

## 2. 转换第一篇文章

复制一条公开文章链接，直接交给 MagicMD。它会自动提取正文、清理代码块、处理媒体资源和来源信息：

```bash
magicmd "https://mp.weixin.qq.com/s/example"
```

也可以显式指定输出目录：

```bash
magicmd convert "https://juejin.cn/post/example" -o output/
```

## 3. 打开生成结果

默认会生成一个内容包目录：

```text
output/article-title/
├── article.md
├── metadata.json
├── extraction-report.json
└── images/
    ├── img_001.png
    └── img_002.png
```

`article.md` 是深度清理后的正文，`metadata.json` 是文章元信息，`extraction-report.json` 是转换报告。报告里会记录 warning、媒体下载结果和需要人工复核的地方。

## 4. 批量转换

把要转换的链接放进 `urls.txt`，一次性批量生成内容包：

```text
https://mp.weixin.qq.com/s/example
https://juejin.cn/post/example
https://blog.csdn.net/user/article/details/123
```

运行批量任务：

```bash
magicmd batch urls.txt -o output/
```

断点续跑时可以跳过已经存在的内容包：

```bash
magicmd batch urls.txt -o output/ --skip-existing
```

## 5. 使用配置文件

如果你要把文章发布到 Hugo、Docusaurus 或自己的知识库，建议先生成一份配置，自定义目录、文件名、metadata 和媒体路径：

```bash
cp .magicmd.example.toml .magicmd.toml
magicmd "https://mp.weixin.qq.com/s/example" --config .magicmd.toml
```

也可以直接用 [配置生成器](/config-builder) 选择发布目标、文件命名和媒体路径，再把生成的 `.magicmd.toml` 放到项目根目录。

## 6. 在程序里调用

如果你要把 MagicMD 接入自己的 Python 后端、CMS、HaoGit 或定时任务，不需要解析 CLI 输出。直接使用 [SDK 接入](/sdk)，调用 `from magicmd import convert_article`，拿到结构化的 Markdown、metadata、图片和转换报告。
