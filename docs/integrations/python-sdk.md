# Python SDK Integration

中文 | English below

MagicMD 不只是 CLI。其他 Python 项目可以直接 `import magicmd`，把公开文章链接转换成结构化结果，再按自己的业务规则入库、重写媒体路径或发布到站点。

SDK 的定位很明确：

- 不启动额外 HTTP 服务。
- 不包含 HaoGit、Django、Hugo 或其他业务系统的专属字段。
- CLI 继续复用同一套转换逻辑。
- 返回结构化对象，方便 Web 后端、定时任务和 Agent Runtime 使用。

## 安装

在外部项目中安装 MagicMD：

```bash
uv add magicmd
# 或
pip install magicmd
```

如果你在 MagicMD 源码仓库内开发：

```bash
uv sync --extra dev
```

## 只在内存中转换

`output_dir=None` 时，MagicMD 不会强制落盘。适合后端先做预览、去重、审核或直接写入数据库。

```python
from magicmd import convert_article

result = convert_article(
    url="https://mp.weixin.qq.com/s/example",
    platform="auto",
    output_dir=None,
    download_images=True,
    config_path=None,
)

print(result.title)
print(result.markdown)
print(result.content_hash)
```

注意：没有 `output_dir` 时，图片不会下载到本地，`images[].local_path` 为空；`images[].markdown_path` 仍表示 Markdown 中当前引用的路径。

## 转换并写出内容包

`output_dir` 有值时，MagicMD 会写出 `article.md`、`metadata.json`、`extraction-report.json`，并按配置下载图片。

```python
from magicmd import convert_article

result = convert_article(
    url="https://juejin.cn/post/example",
    output_dir="output",
)

print(result.package_dir)
print(result.images)
```

## 返回对象

`convert_article()` 返回 `ArticleConversionResult`，这是一个稳定、易序列化的 Pydantic model。

| 字段            | 说明                                               |
| --------------- | -------------------------------------------------- |
| `title`         | 文章标题。                                         |
| `author`        | 作者或账号名。                                     |
| `platform`      | `wechat`、`juejin`、`csdn`、`generic` 等平台标识。 |
| `source_url`    | 调用方传入的原始 URL。                             |
| `canonical_url` | 解析后可识别的规范 URL。                           |
| `published_at`  | 发布时间，能提取到时返回 ISO 字符串。              |
| `excerpt`       | 摘要或页面描述。                                   |
| `markdown`      | 转换后的 Markdown 正文。                           |
| `content_hash`  | 基于内容生成的 hash，适合去重。                    |
| `images`        | 图片资产列表。                                     |
| `warnings`      | 抓取、解析、媒体下载或质量检查中的 warning。       |
| `metadata`      | 与 `metadata.json` 对齐的结构化数据。              |
| `report`        | 与 `extraction-report.json` 对齐的转换报告。       |
| `package_dir`   | 写出内容包时的目录；内存模式为空。                 |

图片资产字段：

| 字段            | 说明                                                                |
| --------------- | ------------------------------------------------------------------- |
| `source_url`    | 原始远程图片 URL。                                                  |
| `local_path`    | 写出内容包后，本机上的图片文件路径。没有下载时为空。                |
| `markdown_path` | Markdown 中实际引用的路径。外部系统复制图片后，可以用它作为替换源。 |
| `alt`           | 图片 alt 文本。                                                     |

序列化示例：

```python
payload = result.model_dump(mode="json")
```

## 错误处理

Web 后端建议捕获明确错误类型，把它们映射成自己的任务状态或 HTTP 响应。

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
    # URL 不属于当前支持的平台。
    raise
except FetchError:
    # 页面抓取失败，例如网络、403、渲染超时。
    raise
except ParseError:
    # HTML 已拿到，但没有解析成有效文章。
    raise
except MediaDownloadError:
    # 媒体下载阶段失败。
    raise
except ConversionError:
    # 其他转换阶段错误。
    raise
```

## 后端接入建议

- 把转换放到后台任务里，避免用户请求一直等待浏览器抓取。
- 用 `content_hash` 做去重，避免同一篇文章重复入库。
- 保存 `warnings` 和 `report`，方便排查平台页面变化。
- 如果要把图片放进自己的 media 目录，先用 `output_dir` 生成本地图片，再根据 `images[].markdown_path` 重写 Markdown。
- 不要依赖网页端登录态、付费内容或验证码页面。MagicMD 面向公开文章链接。

## 示例

在 MagicMD 源码仓库内运行示例：

```bash
uv run python examples/python/convert_to_json.py "https://mp.weixin.qq.com/s/example"
uv run python examples/python/convert_for_cms.py "https://mp.weixin.qq.com/s/example"
```

---

# Python SDK Integration

MagicMD is not only a CLI. Python projects can import `magicmd`, convert public article URLs into structured results, and then store Markdown, rewrite media paths, or publish the content using their own application rules.

The SDK has a narrow contract:

- No extra HTTP service is started.
- No HaoGit, Django, Hugo, or app-specific fields are baked into MagicMD.
- The CLI keeps reusing the same conversion logic.
- The return value is structured and easy to serialize.

## Install

```bash
uv add magicmd
# or
pip install magicmd
```

For local MagicMD development:

```bash
uv sync --extra dev
```

## In-memory conversion

When `output_dir=None`, MagicMD does not force disk output. This is useful for previews, deduplication, review queues, or direct database writes.

```python
from magicmd import convert_article

result = convert_article(
    url="https://mp.weixin.qq.com/s/example",
    platform="auto",
    output_dir=None,
    download_images=True,
    config_path=None,
)

print(result.title)
print(result.markdown)
print(result.content_hash)
```

Without `output_dir`, images are not downloaded locally. `images[].local_path` will be empty, while `images[].markdown_path` still means the path currently referenced in Markdown.

## Write a package

When `output_dir` is set, MagicMD writes `article.md`, `metadata.json`, `extraction-report.json`, and downloaded images according to config.

```python
from magicmd import convert_article

result = convert_article(
    url="https://juejin.cn/post/example",
    output_dir="output",
)

print(result.package_dir)
print(result.images)
```

## Result model

`convert_article()` returns `ArticleConversionResult`, a stable, serializable Pydantic model.

| Field           | Meaning                                                        |
| --------------- | -------------------------------------------------------------- |
| `title`         | Article title.                                                 |
| `author`        | Author or account name.                                        |
| `platform`      | Platform key such as `wechat`, `juejin`, `csdn`, or `generic`. |
| `source_url`    | Original input URL.                                            |
| `canonical_url` | Canonical URL after parsing.                                   |
| `published_at`  | Publish time when available.                                   |
| `excerpt`       | Extracted summary or page description.                         |
| `markdown`      | Converted Markdown content.                                    |
| `content_hash`  | Content hash for deduplication.                                |
| `images`        | Structured image assets.                                       |
| `warnings`      | Fetch, parse, media, or quality warnings.                      |
| `metadata`      | Structured data aligned with `metadata.json`.                  |
| `report`        | Extraction report aligned with `extraction-report.json`.       |
| `package_dir`   | Output package path when a package is written.                 |

Image asset fields:

| Field           | Meaning                                                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `source_url`    | Original remote image URL.                                                                                                     |
| `local_path`    | Downloaded filesystem path when available.                                                                                     |
| `markdown_path` | The path currently referenced by Markdown. Use this as the replacement source when moving files into your own media directory. |
| `alt`           | Image alt text.                                                                                                                |

Serialize with:

```python
payload = result.model_dump(mode="json")
```

## Error handling

Backend code should catch explicit errors and map them to task states or HTTP responses.

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
    raise
except FetchError:
    raise
except ParseError:
    raise
except MediaDownloadError:
    raise
except ConversionError:
    raise
```

## Backend notes

- Run conversion in a background job when browser rendering may take time.
- Use `content_hash` for deduplication.
- Keep `warnings` and `report` for debugging platform changes.
- To move images into your own media storage, write a package first, copy files from `images[].local_path`, then rewrite Markdown using `images[].markdown_path`.
- Do not depend on logged-in pages, paywalled content, or CAPTCHA pages. MagicMD targets public article URLs.

## Examples

```bash
uv run python examples/python/convert_to_json.py "https://mp.weixin.qq.com/s/example"
uv run python examples/python/convert_for_cms.py "https://mp.weixin.qq.com/s/example"
```
