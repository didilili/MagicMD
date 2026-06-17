# HaoGit Import Notes

这份文档只描述集成边界和数据映射，不把 HaoGit 业务逻辑写进 MagicMD。MagicMD 仍然是独立产品：它负责把公开文章链接转换成 Markdown、媒体资产和报告；HaoGit 或其他系统负责入库、审核、实体抽取和发布。

## 推荐流程

```text
用户提交文章 URL
  ↓
后台任务调用 MagicMD SDK
  ↓
生成 Markdown、metadata、report、图片资产
  ↓
按 content_hash 去重
  ↓
复制图片到业务系统 media 目录
  ↓
用 images[].markdown_path 重写 Markdown 图片链接
  ↓
保存 Article 记录
  ↓
后续任务提取 GitHub 仓库、AI 产品、标签、摘要和推荐理由
```

## SDK 调用

```python
from pathlib import Path

from magicmd import convert_article

workdir = Path("/tmp/magicmd-import")

result = convert_article(
    url="https://mp.weixin.qq.com/s/example",
    platform="auto",
    output_dir=workdir,
    download_images=True,
)
```

建议 HaoGit 一类的业务系统使用 `output_dir`，因为图片需要先落到本地，后续才能复制到 Django media、对象存储或静态资源目录。

## 字段映射建议

| MagicMD 字段                                | 业务系统字段建议            | 说明                            |
| ------------------------------------------- | --------------------------- | ------------------------------- |
| `result.title`                              | `Article.title`             | 文章标题。                      |
| `result.author`                             | `Article.author_name`       | 作者、公众号或平台账号。        |
| `result.platform`                           | `Article.source_platform`   | `wechat`、`juejin`、`csdn` 等。 |
| `result.canonical_url or result.source_url` | `Article.source_url`        | 优先保存规范 URL。              |
| `result.published_at`                       | `Article.published_at`      | 可为空。                        |
| `result.markdown`                           | `Article.markdown`          | 重写媒体链接后再保存。          |
| `result.excerpt`                            | `Article.summary_raw`       | 可作为后续摘要任务输入。        |
| `result.content_hash`                       | `Article.content_hash`      | 去重用。                        |
| `result.warnings`                           | `Article.import_warnings`   | 方便人工复核。                  |
| `result.report`                             | `Article.extraction_report` | 保留完整转换报告。              |
| `result.images`                             | `ArticleMedia` 或媒体表     | 每张图一条记录。                |

## 图片复制与 Markdown 重写

`ConvertedImage.markdown_path` 表示当前 Markdown 中实际引用的路径，例如 `images/img_001.png`。业务系统把图片复制到自己的媒体目录后，用这个路径替换成新的公开访问路径。

```python
from pathlib import Path
from shutil import copy2


def move_images_for_cms(result, media_root: Path, media_url_prefix: str) -> tuple[str, list[dict]]:
    target_dir = media_root / result.content_hash
    target_dir.mkdir(parents=True, exist_ok=True)

    markdown = result.markdown
    media_rows = []

    for image in result.images:
        if not image.local_path:
            continue

        source_path = Path(image.local_path)
        target_path = target_dir / source_path.name
        copy2(source_path, target_path)

        public_url = f"{media_url_prefix.rstrip('/')}/{result.content_hash}/{source_path.name}"
        markdown = markdown.replace(image.markdown_path, public_url)

        media_rows.append(
            {
                "source_url": image.source_url,
                "storage_path": str(target_path),
                "public_url": public_url,
                "alt": image.alt,
            }
        )

    return markdown, media_rows
```

## 后续抽取建议

MagicMD 不做业务实体抽取，但它提供了稳定输入。HaoGit 可以在文章入库后再启动任务：

- 从 Markdown 中识别 GitHub 仓库链接。
- 从正文中识别 AI 产品、开源项目、作者、标签和关键词。
- 用 `content_hash` 避免重复抽取。
- 把 `warnings` 非空的文章放入人工复核队列。
- 保存 `report`，当某个平台页面改版时可以回溯定位。

## 边界

- MagicMD 面向公开文章链接，不负责绕过登录、验证码或付费墙。
- MagicMD 不应该知道 HaoGit 的表结构、字段名或推荐算法。
- HaoGit 不应该解析 CLI 文本输出；直接使用 SDK 结果更稳。
- 如果平台页面变化导致转换质量下降，优先补 MagicMD 平台适配和回归样本。
