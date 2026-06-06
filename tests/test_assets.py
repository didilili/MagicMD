from pagemd.assets import infer_image_extension, rewrite_markdown_image_links
from pagemd.models import ImageAsset


def test_infer_image_extension_from_wechat_url():
    assert infer_image_extension("https://example.com/img?wx_fmt=jpeg") == "jpg"


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

