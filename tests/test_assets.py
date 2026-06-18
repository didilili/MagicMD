import httpx
import struct
import zlib

from magicmd.assets import (
    download_images,
    download_videos,
    infer_image_extension,
    rewrite_markdown_image_links,
)
from magicmd.models import Article, ExtractionInfo, ImageAsset


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _gray_alpha_png(width: int, height: int, gray: int, alpha: int) -> bytes:
    raw = b"".join(b"\x00" + bytes([gray, alpha]) * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk("IHDR".encode(), struct.pack(">IIBBBBB", width, height, 8, 4, 0, 0, 0))
        + _png_chunk("IDAT".encode(), zlib.compress(raw))
        + _png_chunk("IEND".encode(), b"")
    )


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

    assert (
        rewrite_markdown_image_links(markdown, images)
        == "正文\n\n![alt](images/img_001.png)\n\n后文"
    )


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
    monkeypatch.setattr("magicmd.assets._image_transport", lambda: httpx.MockTransport(handler))

    next_article = download_images(
        article,
        tmp_path,
        image_dir_name="images",
        filename_pattern="asset-{index}.{ext}",
    )

    assert (tmp_path / "images" / "asset-1.jpg").exists()
    assert next_article.images[0].local_path == "images/asset-1.jpg"
    assert "![Image](images/asset-1.jpg)" in next_article.content_markdown


def test_download_images_honors_markdown_path_template(monkeypatch, tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "image/png"}, content=b"image")

    article = Article(
        title="图片路径文章",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="![Image](https://example.com/a.png)",
        images=[ImageAsset(source_url="https://example.com/a.png")],
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    monkeypatch.setattr("magicmd.assets._image_transport", lambda: httpx.MockTransport(handler))

    next_article = download_images(
        article,
        tmp_path,
        image_dir_name="assets/images",
        filename_pattern="cover_{index:02d}.{ext}",
        markdown_path_pattern="/static/{directory}/{filename}",
    )

    assert (tmp_path / "assets" / "images" / "cover_01.png").exists()
    assert next_article.images[0].local_path == "/static/assets/images/cover_01.png"
    assert "![Image](/static/assets/images/cover_01.png)" in next_article.content_markdown


def test_download_images_saves_cover_images_without_rewriting_markdown(monkeypatch, tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"image")

    article = Article(
        title="封面文章",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文\n\n![Image](https://example.com/body.jpg)",
        cover_image=ImageAsset(source_url="https://example.com/cover.jpg", alt="cover"),
        share_cover_image=ImageAsset(source_url="https://example.com/share.jpg", alt="share cover"),
        images=[ImageAsset(source_url="https://example.com/body.jpg")],
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    monkeypatch.setattr("magicmd.assets._image_transport", lambda: httpx.MockTransport(handler))

    next_article = download_images(article, tmp_path)

    assert (tmp_path / "images" / "img_001.jpg").exists()
    assert (tmp_path / "images" / "cover.jpg").exists()
    assert (tmp_path / "images" / "share_cover.jpg").exists()
    assert next_article.images[0].local_path == "images/img_001.jpg"
    assert next_article.cover_image is not None
    assert next_article.cover_image.local_path == "images/cover.jpg"
    assert next_article.share_cover_image is not None
    assert next_article.share_cover_image.local_path == "images/share_cover.jpg"
    assert "![Image](images/img_001.jpg)" in next_article.content_markdown
    assert "cover.jpg" not in next_article.content_markdown
    assert "share_cover.jpg" not in next_article.content_markdown


def test_download_images_saves_cover_images_without_touching_markdown_when_body_has_no_images(
    monkeypatch, tmp_path
):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"image")

    article = Article(
        title="纯封面文章",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="正文\n\n",
        cover_image=ImageAsset(source_url="https://example.com/cover.jpg", alt="cover"),
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    monkeypatch.setattr("magicmd.assets._image_transport", lambda: httpx.MockTransport(handler))

    next_article = download_images(article, tmp_path)

    assert (tmp_path / "images" / "cover.jpg").exists()
    assert next_article.cover_image is not None
    assert next_article.cover_image.local_path == "images/cover.jpg"
    assert next_article.content_markdown == "正文\n\n"


def test_download_images_keeps_pngs_invisible_on_white_background(monkeypatch, tmp_path):
    invisible_png = _gray_alpha_png(4, 4, gray=255, alpha=255)

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == "https://example.com/decor.png":
            return httpx.Response(200, headers={"content-type": "image/png"}, content=invisible_png)
        return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"jpg")

    article = Article(
        title="海报模板文章",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown=(
            "![Image](https://example.com/decor.png)\n\n![Image](https://example.com/content.jpg)"
        ),
        images=[
            ImageAsset(source_url="https://example.com/decor.png"),
            ImageAsset(source_url="https://example.com/content.jpg"),
        ],
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )
    monkeypatch.setattr("magicmd.assets._image_transport", lambda: httpx.MockTransport(handler))

    next_article = download_images(article, tmp_path)

    assert "![Image](images/img_001.png)" in next_article.content_markdown
    assert "![Image](images/img_002.jpg)" in next_article.content_markdown
    assert [image.source_url for image in next_article.images] == [
        "https://example.com/decor.png",
        "https://example.com/content.jpg",
    ]
    assert (tmp_path / "images" / "img_001.png").exists()
    assert (tmp_path / "images" / "img_002.jpg").exists()


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

    monkeypatch.setattr("magicmd.assets._video_transport", lambda: httpx.MockTransport(handler))

    next_article = download_videos(article, tmp_path)

    assert next_article.content_markdown == "[视频](videos/video_001.mp4)"
    assert (tmp_path / "videos" / "video_001.mp4").read_bytes() == b"mp4-data"


def test_download_videos_honors_media_path_templates(monkeypatch, tmp_path):
    article = Article(
        title="视频路径文章",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        content_markdown="[视频](https://mpvideo.qpic.cn/demo.mp4)",
        extraction=ExtractionInfo(platform="wechat", parser="wechat"),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "video/mp4"}, content=b"mp4-data")

    monkeypatch.setattr("magicmd.assets._video_transport", lambda: httpx.MockTransport(handler))

    next_article = download_videos(
        article,
        tmp_path,
        video_dir_name="assets/videos",
        filename_pattern="clip_{index:02d}.{ext}",
        markdown_path_pattern="/static/{directory}/{filename}",
    )

    assert next_article.content_markdown == "[视频](/static/assets/videos/clip_01.mp4)"
    assert (tmp_path / "assets" / "videos" / "clip_01.mp4").read_bytes() == b"mp4-data"
