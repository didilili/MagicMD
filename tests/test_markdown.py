from magicmd.config import MarkdownConfig
from magicmd.models import Article, ExtractionInfo, ImageAsset
from magicmd import quality
from magicmd.platforms.shared.markdown import html_to_markdown
from magicmd.platforms.shared.markdown import _normalize_markdown_emphasis
from magicmd.renderers.markdown import render_markdown


def test_render_markdown_includes_front_matter_and_source_block():
    article = Article(
        title="Codex 实战",
        author="HaoGit",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-06T12:00:00+08:00",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    md = render_markdown(article)

    assert 'title: "Codex 实战"' in md
    assert 'platform: "wechat"' in md
    assert "# Codex 实战" in md
    assert "> Original: https://mp.weixin.qq.com/s/demo" in md
    assert md.rstrip().endswith("正文")


def test_render_markdown_uses_configured_front_matter_and_source_block():
    article = Article(
        title="Codex 实战",
        author="HaoGit",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-06T12:00:00+08:00",
        content_markdown="正文",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    config = MarkdownConfig(
        include_title=False,
        front_matter_fields={"title": "{title}", "url": "{source_url}"},
        source_block_template="> Saved from {source_url}",
    )

    md = render_markdown(article, config)

    assert 'title: "Codex 实战"' in md
    assert 'url: "https://mp.weixin.qq.com/s/demo"' in md
    assert 'platform: "wechat"' not in md
    assert "# Codex 实战" not in md
    assert "> Saved from https://mp.weixin.qq.com/s/demo" in md
    assert "> Original: https://mp.weixin.qq.com/s/demo" not in md


def test_render_markdown_includes_wechat_cover_image_after_source_block():
    article = Article(
        title="招生公告",
        author="实验幼儿园",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-15T12:00:00+08:00",
        content_markdown="正文第一段",
        cover_image=ImageAsset(
            source_url="https://mmbiz.qpic.cn/cover/0?wx_fmt=jpeg",
            local_path="images/cover.jpg",
            alt="cover",
        ),
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    md = render_markdown(article)

    assert (
        "> Original: https://mp.weixin.qq.com/s/demo\n\n"
        "---\n\n"
        "![cover](images/cover.jpg)\n\n"
        "---\n\n"
        "正文第一段"
    ) in md


def test_render_markdown_can_disable_wechat_cover_image():
    article = Article(
        title="招生公告",
        author="实验幼儿园",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文第一段",
        cover_image=ImageAsset(
            source_url="https://mmbiz.qpic.cn/cover/0?wx_fmt=jpeg",
            local_path="images/cover.jpg",
            alt="cover",
        ),
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    md = render_markdown(article, MarkdownConfig(include_cover_image=False))

    assert "![cover](images/cover.jpg)" not in md
    assert md.rstrip().endswith("正文第一段")


def test_render_markdown_uses_remote_cover_when_local_path_is_missing():
    article = Article(
        title="招生公告",
        author="实验幼儿园",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文第一段",
        cover_image=ImageAsset(
            source_url="https://mmbiz.qpic.cn/cover/0?wx_fmt=jpeg",
            alt="cover",
        ),
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    md = render_markdown(article)

    assert "![cover](https://mmbiz.qpic.cn/cover/0?wx_fmt=jpeg)" in md


def test_html_to_markdown_removes_empty_image_with_nonempty_alt():
    assert html_to_markdown('<p>前文</p><img alt="Image"><p>后文</p>') == "前文\n\n后文"


def test_repair_markdown_quality_unwraps_single_line_address_fence():
    markdown = "```javascript\n开源地址：https://github.com/example/demo\n```"

    assert (
        quality.repair_markdown_quality(markdown)
        == "开源地址：<https://github.com/example/demo>"
    )


def test_repair_markdown_quality_repairs_paired_escaped_strong_in_prose():
    assert (
        quality.repair_markdown_quality(r"正文 \*\*重点\*\* 结束")
        == "正文 **重点** 结束"
    )
    assert quality.repair_markdown_quality(r"正文 \*\*未闭合") == r"正文 \*\*未闭合"


def test_repair_markdown_quality_keeps_escaped_strong_in_code():
    markdown = (
        "正文 `value = r'\\*\\*重点\\*\\*'` 结束\n\n"
        "```python\n"
        "value = r'\\*\\*重点\\*\\*'\n"
        "```"
    )

    assert quality.repair_markdown_quality(markdown) == markdown


def test_repair_markdown_quality_keeps_unrelated_outer_whitespace():
    markdown = "\n正文没有需要修复的格式。\n"

    assert quality.repair_markdown_quality(markdown) == markdown


def test_normalize_markdown_emphasis_removes_orphan_markers_around_images():
    markdown = """
正文

**

![Image](images/example.png)

**

后文
""".strip()

    normalized = _normalize_markdown_emphasis(markdown)

    assert normalized == "正文\n\n![Image](images/example.png)\n\n后文"


def test_normalize_markdown_emphasis_cleans_partial_image_and_redundant_markers():
    markdown = """
**

![Image](images/example.png)

**摄像头气泡****

**重要说明**正文。****
""".strip()

    normalized = _normalize_markdown_emphasis(markdown)

    assert normalized == (
        "![Image](images/example.png)\n\n"
        "**摄像头气泡**\n\n"
        "**重要说明**正文。"
    )


def test_normalize_markdown_emphasis_removes_unmatched_bold_inside_italics():
    markdown = "提示词：*帮我生成一个页面，而且**要有一键复原按钮。*"

    normalized = _normalize_markdown_emphasis(markdown)

    assert normalized == "提示词：*帮我生成一个页面，而且要有一键复原按钮。*"
