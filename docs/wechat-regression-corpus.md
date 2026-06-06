# 微信公众号回归测试集 / WeChat Regression Corpus

## 目的

这份回归测试集用于沉淀真实微信公众号文章转换中出现过的格式问题。每当 MagicMD 修改微信公众号解析、Markdown 清洗、图片下载或批量转换逻辑时，都应该用这批样本重新转换，并结合 `batch-report.md` 做人工抽查。

The corpus records real WeChat formatting issues observed during MagicMD conversion. Re-run it after parser, Markdown cleanup, media download, or batch conversion changes, then review `batch-report.md` together with manual spot checks.

## 文件

- `tests/fixtures/wechat_regression_manifest.json`: 真实文章 URL 与问题标签清单。
- `batch-report.json`: 批量转换后的机器可读质量报告。
- `batch-report.md`: 批量转换后的人工阅读报告。

## 运行方式

把 manifest 中的 URL 复制到一个临时 URL 文件，或维护一个本地不提交的 `urls-regression.txt`：

```bash
uv run magicmd batch urls-regression.txt -o output/wechat-regression-v0.1
```

转换完成后优先查看：

```text
output/wechat-regression-v0.1/batch-report.md
output/wechat-regression-v0.1/batch-report.json
```

## 当前重点问题标签

| 标签 | 说明 |
| --- | --- |
| `video_extraction` | 微信视频提取、占位、下载和链接可访问性。 |
| `linked_image` | 图片外层超链接是否保留，Markdown 是否断裂。 |
| `non_code_pre` | 非代码样式块不应被误转成代码块。 |
| `fragmented_bold` | 微信富文本把一个加粗词拆成多个 span 时，Markdown 加粗应合并。 |
| `decorative_gif` | 动态修饰图、空白小 GIF、占位图不应输出成正文图片。 |
| `wide_block_link` | 整段外层链接应收窄到真正有链接样式的文字范围。 |
| `layout_heading` | 视觉排版容器不应误升格为 Markdown 标题。 |

## v0.1 验收建议

- 所有 URL 批量转换可以跑完，即使个别链接失败也要进入报告。
- `batch-report.md` 中 `Failed`、`With warnings`、`With quality issues` 三项需要逐条看。
- 对重点样本再打开 `article.md` 目测：正文顺序、图片位置、链接范围、加粗、视频、推荐阅读区。
- 如果发现新的格式问题，把 URL 和现象追加到 manifest 的 `issue_tags`，再新增针对性的单元测试。
