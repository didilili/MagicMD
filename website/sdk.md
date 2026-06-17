---
title: SDK 接入
description: 在 Python 项目中直接调用 MagicMD，把公开文章链接转换成结构化 Markdown 结果。
---

# SDK 接入

MagicMD 已经支持 Python SDK。也就是说，你不一定要在终端里运行 `magicmd` 命令；Web 后端、CMS、定时任务或 Agent Runtime 可以直接 `import magicmd`，把公开文章链接转换成结构化结果。

适合用 SDK 的场景：

- 用户在你的系统里提交一条文章 URL。
- 后台任务自动转换文章并入库。
- CMS、Django、HaoGit 或自己的内容系统需要保存 Markdown、metadata 和图片。
- Agent 工作流需要稳定拿到标题、正文、来源信息、warning 和转换报告。

如果你只是自己手动转换文章，先看 [快速开始](/quick-start)。如果你要把 MagicMD 接到另一个 Python 项目里，再看这一页。

## 安装

在你的 Python 项目里安装 MagicMD：

```bash
uv add magicmd
```

也可以使用 pip：

```bash
pip install magicmd
```

## 最小调用

只在内存里拿到转换结果，不强制写出内容包：

```python
from magicmd import convert_article

result = convert_article(
    url="https://mp.weixin.qq.com/s/example",
    output_dir=None,
)

print(result.title)
print(result.markdown)
print(result.metadata)
```

`output_dir=None` 适合预览、去重、审核或直接写入数据库。这个模式不会把图片下载到本地。

## 写出内容包

如果你的系统需要复制图片、保留报告或方便人工复核，建议传入 `output_dir`：

```python
from magicmd import convert_article

result = convert_article(
    url="https://juejin.cn/post/example",
    output_dir="output/import-workdir",
    download_images=True,
)

print(result.package_dir)
print(result.images)
print(result.report)
```

这会生成和 CLI 一样的内容包：`article.md`、`metadata.json`、`extraction-report.json` 和媒体目录。

## 返回字段

`convert_article()` 返回 `ArticleConversionResult`。常用字段包括：

| 字段                           | 说明                                                   |
| ------------------------------ | ------------------------------------------------------ |
| `title`                        | 文章标题。                                             |
| `author`                       | 作者、公众号或平台账号。                               |
| `platform`                     | 平台标识，例如 `wechat`、`juejin`、`csdn`、`generic`。 |
| `source_url` / `canonical_url` | 原始链接和规范链接。                                   |
| `published_at`                 | 发布时间，能提取到时返回。                             |
| `markdown`                     | 转换后的 Markdown 正文。                               |
| `content_hash`                 | 基于正文内容生成的 hash，适合去重。                    |
| `images`                       | 图片资产列表。                                         |
| `warnings`                     | 抓取、解析或媒体下载中的 warning。                     |
| `metadata`                     | 与 `metadata.json` 对齐的结构化数据。                  |
| `report`                       | 与 `extraction-report.json` 对齐的转换报告。           |
| `package_dir`                  | 写出内容包时的目录；内存模式为空。                     |

图片字段里最容易混淆的是这两个：

| 字段            | 说明                                |
| --------------- | ----------------------------------- |
| `markdown_path` | Markdown 正文里当前引用的图片路径。 |
| `local_path`    | 图片下载到本机后的真实文件路径。    |

外部系统通常先把 `local_path` 对应的文件复制到自己的 media 目录，再用新的公开 URL 替换 Markdown 里的 `markdown_path`。

## 错误处理

SDK 会按阶段抛出明确错误，方便你映射成自己的任务状态：

```python
from magicmd import (
    ConversionError,
    FetchError,
    MediaDownloadError,
    ParseError,
    UnsupportedPlatformError,
    convert_article,
)

try:
    result = convert_article("https://mp.weixin.qq.com/s/example", output_dir="output")
except UnsupportedPlatformError:
    # 当前 URL 不属于已支持平台，或平台被配置禁用。
    raise
except FetchError:
    # 页面抓取失败，例如网络错误、403、浏览器渲染超时。
    raise
except ParseError:
    # HTML 已拿到，但没有解析成有效文章。
    raise
except MediaDownloadError:
    # 媒体下载阶段失败。
    raise
except ConversionError:
    # 配置、写入或其他转换阶段错误。
    raise
```

## 接入建议

- 把转换放到后台任务里，避免用户请求长时间等待。
- 用 `content_hash` 做去重。
- 保存 `warnings` 和 `report`，方便排查平台页面变化。
- 需要本地图片时，使用 `output_dir`，再复制 `images[].local_path`。
- 不要依赖登录态、付费内容、验证码或私有页面；MagicMD 面向公开文章链接。

更多细节见仓库里的 [Python SDK Integration](https://github.com/didilili/MagicMD/blob/main/docs/integrations/python-sdk.md) 和 [HaoGit Import Notes](https://github.com/didilili/MagicMD/blob/main/docs/integrations/haogit-import.md)。
