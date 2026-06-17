from __future__ import annotations

DEFAULT_LANGUAGE = "zh-CN"

_LANGUAGE_ALIASES = {
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_cn": "zh-CN",
    "cn": "zh-CN",
    "chinese": "zh-CN",
    "en": "en-US",
    "en-us": "en-US",
    "en_us": "en-US",
    "english": "en-US",
}

_MESSAGES = {
    "zh-CN": {
        "detecting_platform": "识别平台",
        "fetching_article": "抓取文章（{platform}）",
        "parsing_article": "解析文章",
        "writing_package": "写入 Markdown 内容包",
        "rendering_markdown": "渲染 Markdown",
        "downloading_media": "下载媒体资源",
        "skipping_media": "跳过图片下载",
        "saving_report": "保存转换报告",
        "preparing_report": "准备转换报告",
        "created_package": "已生成内容包：{path}",
        "batch_skipped": "跳过 {url} -> {path}",
        "batch_ok": "完成 {url} -> {path}",
        "batch_failed": "失败 {url}: {error}",
        "batch_report": "批量报告：{path}",
    },
    "en-US": {
        "detecting_platform": "Detecting platform",
        "fetching_article": "Fetching article ({platform})",
        "parsing_article": "Parsing article",
        "writing_package": "Writing Markdown package",
        "rendering_markdown": "Rendering Markdown",
        "downloading_media": "Downloading media",
        "skipping_media": "Skipping image download",
        "saving_report": "Saving extraction report",
        "preparing_report": "Preparing extraction report",
        "created_package": "Created output package: {path}",
        "batch_skipped": "SKIP {url} -> {path}",
        "batch_ok": "OK {url} -> {path}",
        "batch_failed": "FAIL {url}: {error}",
        "batch_report": "Batch report: {path}",
    },
}


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE
    normalized = _LANGUAGE_ALIASES.get(language.strip().lower())
    return normalized or DEFAULT_LANGUAGE


def ui_text(language: str | None, key: str, **values: object) -> str:
    normalized = normalize_language(language)
    template = _MESSAGES[normalized][key]
    return template.format(**values)
