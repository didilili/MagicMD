import httpx

from pagemd.assets import (
    download_images,
    download_videos,
    infer_image_extension,
    rewrite_markdown_image_links,
)
from pagemd.models import Article, ExtractionInfo, ImageAsset


def test_infer_image_extension_from_wechat_url():
    assert infer_image_extension("https://example.com/img?wx_fmt=jpeg") == "jpg"


def test_infer_image_extension_ignores_wechat_other_when_content_type_known():
    assert infer_image_extension("https://example.com/img?wx_fmt=other", "image/jpeg") == "jpg"


def test_rewrite_markdown_image_links_handles_parentheses():
    markdown = "![alt](https://example.com/a_(1).png)"
    images = [
        ImageAsset(
            source_url="https://example.com/a_(1).png",
            local_path="images/img_001.png",
            alt="alt",
        )
    ]

    assert rewrite_markdown_image_links(markdown, images) == "![alt](images/img_001.png)"


def test_rewrite_markdown_image_links_keeps_images_block_separated():
    markdown = "正文![alt](https://example.com/a.png)后文"
    images = [
        ImageAsset(
            source_url="https://example.com/a.png",
            local_path="images/img_001.png",
            alt="alt",
        )
    ]

    assert rewrite_markdown_image_links(markdown, images) == "正文\n\n![alt](images/img_001.png)\n\n后文"


def test_rewrite_markdown_image_links_keeps_linked_images_intact():
    markdown = "[![Image](https://example.com/a.png)](https://mp.weixin.qq.com/mp/appmsgalbum?id=1)"
    images = [
        ImageAsset(
            source_url="https://example.com/a.png",
            local_path="images/img_001.png",
            alt="Image",
        )
    ]

    assert (
        rewrite_markdown_image_links(markdown, images)
        == "[![Image](images/img_001.png)](https://mp.weixin.qq.com/mp/appmsgalbum?id=1)"
    )


def test_download_images_honors_filename_pattern(monkeypatch, tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"image")

    article = Article(
        title="图片命名文章",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="![Image](https://example.com/a.jpg)",
        images=[ImageAsset(source_url="https://example.com/a.jpg")],
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    monkeypatch.setattr("pagemd.assets._image_transport", lambda: httpx.MockTransport(handler))

    next_article = download_images(
        article,
        tmp_path,
        image_dir_name="images",
        filename_pattern="asset-{index}.{ext}",
    )

    assert (tmp_path / "images" / "asset-1.jpg").exists()
    assert next_article.images[0].local_path == "images/asset-1.jpg"
    assert "![Image](images/asset-1.jpg)" in next_article.content_markdown


def test_download_videos_saves_local_file_and_rewrites_markdown(monkeypatch, tmp_path):
    article = Article(
        title="视频文章",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="[视频](https://mpvideo.qpic.cn/demo.f10002.mp4?auth\\_key=abc)",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["referer"] == article.source_url
        assert str(request.url) == "https://mpvideo.qpic.cn/demo.f10002.mp4?auth_key=abc"
        return httpx.Response(200, headers={"content-type": "video/mp4"}, content=b"mp4-data")

    monkeypatch.setattr("pagemd.assets._video_transport", lambda: httpx.MockTransport(handler))

    next_article = download_videos(article, tmp_path)

    assert next_article.content_markdown == "[视频](videos/video_001.mp4)"
    assert (tmp_path / "videos" / "video_001.mp4").read_bytes() == b"mp4-data"
