from magicmd.config import MarkdownConfig
from magicmd.models import Article, ExtractionInfo, ImageAsset
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
