from magicmd.models import Article, ExtractionInfo, ImageAsset


def test_article_metadata_dump_uses_stable_keys():
    article = Article(
        title="Codex 实战",
        author="HaoGit",
        platform="wechat",
        source_url="https://mp.weixin.qq.com/s/demo",
        canonical_url="https://mp.weixin.qq.com/s/demo",
        published_at="2026-06-06T12:00:00+08:00",
        excerpt="摘要",
        content_markdown="正文",
        content_html="<p>正文</p>",
        cover_image=ImageAsset(
            source_url="https://example.com/cover.jpg",
            local_path="images/cover.jpg",
            alt="cover",
        ),
        share_cover_image=ImageAsset(
            source_url="https://example.com/share.jpg",
            local_path="images/share_cover.jpg",
            alt="share cover",
        ),
        images=[
            ImageAsset(
                source_url="https://example.com/a.png",
                local_path="images/img_001.png",
                alt="diagram",
            )
        ],
        extraction=ExtractionInfo(status="success", platform="wechat", parser="wechat"),
    )

    data = article.to_metadata()

    assert data["title"] == "Codex 实战"
    assert data["platform"] == "wechat"
    assert data["cover_image"]["local_path"] == "images/cover.jpg"
    assert data["share_cover_image"]["source_url"] == "https://example.com/share.jpg"
    assert data["images"][0]["local_path"] == "images/img_001.png"
    assert data["extraction"]["status"] == "success"
    assert "content_markdown" not in data
    assert "content_html" not in data


def test_extraction_info_marks_content_not_found_warning_as_failed():
    extraction = ExtractionInfo(
        platform="juejin", parser="juejin", warnings=["juejin_content_not_found"]
    )

    assert extraction.status == "failed"
