from pathlib import Path

from magicmd.platforms.wechat import parse_wechat_html


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_wechat_html_extracts_title_author_body_and_images():
    html = (FIXTURES / "wechat" / "basic.html").read_text(encoding="utf-8")

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/demo")

    assert article.title == "微信文章标题"
    assert article.author == "MagicMD"
    assert article.platform == "wechat"
    assert "第一段正文" in article.content_markdown
    assert 'print("hello")' in article.content_markdown
    assert article.images[0].source_url == "https://example.com/wechat.png"


def test_parse_wechat_html_extracts_cover_images_from_metadata_and_scripts():
    html = """
    <html>
      <head>
        <meta property="og:image" content="http://mmbiz.qpic.cn/cover/0?wx_fmt=jpeg" />
        <script>
          var msg_cdn_url = "http://mmbiz.qpic.cn/fallback/0?wx_fmt=jpeg";
          var cdn_url_1_1 = "http://mmbiz.qpic.cn/share/0?wx_fmt=png";
        </script>
      </head>
      <body>
        <h1 id="activity-name">带封面文章</h1>
        <div id="js_content"><p>正文</p></div>
      </body>
    </html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/cover")

    assert article.cover_image is not None
    assert article.cover_image.source_url == "https://mmbiz.qpic.cn/cover/0?wx_fmt=jpeg"
    assert article.share_cover_image is not None
    assert article.share_cover_image.source_url == "https://mmbiz.qpic.cn/share/0?wx_fmt=png"
    assert "cover/0" not in article.content_markdown


def test_parse_wechat_html_prefers_wechat_wide_cover_over_square_open_graph_image():
    html = """
    <html>
      <head>
        <meta property="og:image" content="https://mmbiz.qpic.cn/square/0?wx_fmt=jpeg" />
        <script>
          var msg_cdn_url = "https://mmbiz.qpic.cn/square/0?wx_fmt=jpeg";
          var cdn_url_1_1 = "https://mmbiz.qpic.cn/square/0?wx_fmt=jpeg";
          cdn_url_235_1 = "https://mmbiz.qpic.cn/wide/0?wx_fmt=jpeg";
        </script>
      </head>
      <body>
        <h1 id="activity-name">横版封面文章</h1>
        <div id="js_content"><p>正文</p></div>
      </body>
    </html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/wide-cover")

    assert article.cover_image is not None
    assert article.cover_image.source_url == "https://mmbiz.qpic.cn/wide/0?wx_fmt=jpeg"
    assert article.share_cover_image is not None
    assert article.share_cover_image.source_url == "https://mmbiz.qpic.cn/square/0?wx_fmt=jpeg"


def test_parse_wechat_html_uses_msg_cdn_url_when_open_graph_cover_is_missing():
    html = """
    <html>
      <head>
        <script>
          var msg_cdn_url = "http://mmbiz.qpic.cn/script-cover/0?wx_fmt=jpeg";
        </script>
      </head>
      <body>
        <h1 id="activity-name">脚本封面文章</h1>
        <div id="js_content"><p>正文</p></div>
      </body>
    </html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/script-cover")

    assert article.cover_image is not None
    assert article.cover_image.source_url == ("https://mmbiz.qpic.cn/script-cover/0?wx_fmt=jpeg")
    assert article.share_cover_image is None


def test_parse_wechat_html_normalizes_rich_sections_styles_and_images():
    html = """
    <html>
      <body>
        <h1 id="activity-name">富文本文章</h1>
        <a id="js_name">MagicMD</a>
        <div id="js_content">
          <section>
            <section style="font-size: 14px;">
              <span style="font-weight: bold;">现在，ChatGPT 的记忆系统更像人了。</span>
            </section>
            <p>OpenAI 近期推出了一套全新的记忆系统。</p>
            <section style="font-weight: 600; font-size: 21px; color:#FD4606;">
              不再从零开始，ChatGPT 全新记忆系统登场
            </section>
            <section><strong>01</strong></section>
            <section><strong>把代码变成知识图谱</strong></section>
            <section style="font-weight: 600; font-size: 21px; color:#00B38B;">
              3<strong>GPU 之外，视频模型还有一张更贵的账单</strong>
            </section>
            <section style="margin-left: 8px; margin-right: 8px; line-height: 2em; margin-bottom: 16px;">
              <strong><span style="font-weight: bold;">andrej-karpathy-skills：</span>根据 Karpathy 观察 LLM 写代码的坑。</strong>
            </section>
            <section style="margin-left: 8px; margin-right: 8px; line-height: 2em; margin-bottom: 16px;">
              <strong><span style="font-weight: bold;">mattpocock/skills：</span>Claude Code 技能包。</strong>
            </section>
            <section><img data-src="https://example.com/cover.png" /></section>
            <section>图片后的下一行文字。</section>
          </section>
        </div>
      </body>
    </html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/rich")

    assert "**现在，ChatGPT 的记忆系统更像人了。**" in article.content_markdown
    assert "## 不再从零开始，ChatGPT 全新记忆系统登场" in article.content_markdown
    assert "## 01 把代码变成知识图谱" in article.content_markdown
    assert "## 3 GPU 之外，视频模型还有一张更贵的账单" in article.content_markdown
    assert (
        "根据 Karpathy 观察 LLM 写代码的坑。**\n\n**mattpocock/skills：" in article.content_markdown
    )
    assert (
        "![Image](https://example.com/cover.png)\n\n图片后的下一行文字。"
        in article.content_markdown
    )


def test_parse_wechat_html_does_not_promote_ordinary_bold_paragraphs_to_headings():
    html = """
    <html><body>
      <h1 id="activity-name">普通强调文章</h1>
      <div id="js_content">
        <p><strong>看完这个新闻，我当时就震惊了：</strong></p>
        <p style="font-size: 20px; font-weight: 400; color: rgb(42, 42, 42);">千问云刚发布没多久。</p>
        <p><strong>很多人觉得这是AI新闻。但我看到的是另一件事：</strong></p>
        <section style="font-weight: 600; font-size: 21px; color:#7A4AEA;">真正的小标题</section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/bold")

    assert "## 看完这个新闻" not in article.content_markdown
    assert "## 千问云刚发布" not in article.content_markdown
    assert "千问云刚发布没多久。" in article.content_markdown
    assert "**看完这个新闻，我当时就震惊了：**" in article.content_markdown
    assert "## 真正的小标题" in article.content_markdown


def test_parse_wechat_html_keeps_large_lazy_images_with_tiny_css_width():
    html = """
    <html><body>
      <h1 id="activity-name">懒加载图片文章</h1>
      <div id="js_content">
        <p>正文前。</p>
        <img data-src="https://example.com/content.png" data-w="651" data-ratio="0.55"
             style="width: 3px !important; height: 1px !important;" />
        <p>正文后。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/image")

    assert "https://example.com/content.png" in article.content_markdown
    assert [img.source_url for img in article.images] == ["https://example.com/content.png"]


def test_parse_wechat_html_handles_linked_images_without_broken_brackets():
    html = """
    <html><body>
      <h1 id="activity-name">链接图片文章</h1>
      <div id="js_content">
        <a href="https://mp.weixin.qq.com/mp/appmsgalbum?album_id=1">
          <img data-src="https://example.com/album.png" />
        </a>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/linked-image")

    assert "[\n\n![Image]" not in article.content_markdown
    assert "\n\n](https://mp.weixin.qq.com/mp/appmsgalbum" not in article.content_markdown
    assert (
        "[![Image](https://example.com/album.png)](https://mp.weixin.qq.com/mp/appmsgalbum?album_id=1)"
        in article.content_markdown
    )


def test_parse_wechat_html_treats_non_code_pre_as_plain_content():
    html = """
    <html><body>
      <h1 id="activity-name">尾部推广文章</h1>
      <div id="js_content">
        <p>你知道的或者使用的在 Linux 终端中的更多网络监视工具还有哪些？</p>
        <pre><section><strong><span>-End-</span></strong></section></pre>
        <pre><section>读到这里说明你喜欢本公众号的文章。</section></pre>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/pre")

    assert "```" not in article.content_markdown
    assert "## -End-" not in article.content_markdown
    assert "**-End-**" in article.content_markdown
    assert "读到这里说明你喜欢本公众号的文章。" in article.content_markdown


def test_parse_wechat_html_cleans_fragmented_bold_recommendation_text():
    html = """
    <html><body>
      <h1 id="activity-name">推荐区文章</h1>
      <div id="js_content">
        <p>
          <strong>推</strong><strong>荐</strong><strong>阅</strong><strong>读</strong>
        </p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/recommend-title")

    assert "**推****荐****阅****读**" not in article.content_markdown
    assert "**推荐阅读**" in article.content_markdown


def test_parse_wechat_html_cleans_bold_italic_numbered_link_list_item():
    html = """
    <html><body>
      <h1 id="activity-name">推荐区文章</h1>
      <div id="js_content">
        <p>
          <strong><em>3.</em></strong><strong><a href="https://example.com/linux">Linux 学习指南 （收藏篇）</a></strong>
        </p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/recommend-link")

    assert "***3.*****[" not in article.content_markdown
    assert "**[Linux 学习指南 （收藏篇）]" not in article.content_markdown
    assert "3. [Linux 学习指南 （收藏篇）](https://example.com/linux)" in article.content_markdown


def test_parse_wechat_html_cleans_heavily_fragmented_bold_text():
    html = """
    <html><body>
      <h1 id="activity-name">碎片加粗文章</h1>
      <div id="js_content">
        <p>
          <strong>第</strong><strong><strong>九十一</strong></strong><strong>号</strong>
        </p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/fragmented-bold")

    assert "******" not in article.content_markdown
    assert "**第九十一号**" in article.content_markdown


def test_parse_wechat_html_filters_tiny_placeholder_background_gifs():
    html = """
    <html><body>
      <h1 id="activity-name">装饰动图文章</h1>
      <div id="js_content">
        <img data-src="https://example.com/header.gif" data-type="gif" data-w="1079" data-ratio="0.216"
             class="rich_pages __bg_gif" style="width: 1px !important;" />
        <img data-src="https://example.com/arrow.gif" data-type="gif" data-w="300" data-ratio="0.74"
             class="js_img_placeholder wx_img_placeholder __bg_gif"
             style="width: 22px !important; height: auto !important;" />
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/decorative-gif")

    assert "https://example.com/header.gif" in article.content_markdown
    assert "https://example.com/arrow.gif" not in article.content_markdown
    assert [image.source_url for image in article.images] == ["https://example.com/header.gif"]


def test_parse_wechat_html_narrows_block_link_to_colored_span():
    html = """
    <html><body>
      <h1 id="activity-name">局部链接文章</h1>
      <div id="js_content">
        <section>
          <a href="https://example.com/rule" title="https://example.com/rule">
            <p>
              <span style="color: rgb(15, 15, 15);">根据相关规定，将视为</span>
              <span style="color: rgb(36, 110, 255);">《微信公众平台运营规范》4.20 第三方商业营销内容违规</span>
              <span style="color: rgb(15, 15, 15);">。平台将按照规范限制。</span>
            </p>
          </a>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/narrow-link")

    assert "[根据相关规定" not in article.content_markdown
    assert "根据相关规定，将视为" in article.content_markdown
    assert (
        "[《微信公众平台运营规范》4.20 第三方商业营销内容违规](https://example.com/rule"
        in article.content_markdown
    )
    assert "。平台将按照规范限制。" in article.content_markdown


def test_parse_wechat_html_keeps_images_wrapped_in_layout_headings():
    html = """
    <html><body>
      <h1 id="activity-name">图片标题容器文章</h1>
      <div id="js_content">
        <h3 style="color: rgb(34, 34, 34); background-color: rgb(255, 255, 255);">
          <section><img data-src="https://example.com/cover.jpg" data-w="1080" data-ratio="0.425" alt="Image" /></section>
        </h3>
        <h3 style="color: rgb(34, 34, 34); background-color: rgb(255, 255, 255);">
          <section><p><strong><span style="font-size: 18px; color: rgb(255, 255, 255); background-color: rgb(127, 127, 127);">新智元报道</span></strong></p></section>
        </h3>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/layout-heading-image")

    assert "### Image" not in article.content_markdown
    assert "### 新智元报道" not in article.content_markdown
    assert "![Image](https://example.com/cover.jpg)" in article.content_markdown
    assert "**新智元报道**" in article.content_markdown
    assert article.images[0].source_url == "https://example.com/cover.jpg"


def test_parse_wechat_html_treats_intro_card_heading_as_plain_text():
    html = """
    <html><body>
      <h1 id="activity-name">导读卡片文章</h1>
      <div id="js_content">
        <section>
          <h5 style="margin: 10px 8px 0px; padding: 10px; font-size: 14px; background-color: rgb(248, 248, 248); color: rgb(0, 0, 0); line-height: 1.75em;">
            <span><strong>【新智元导读】</strong>这是一段导读文字，不应该成为五级标题。</span>
          </h5>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/intro-card")

    assert "##### 【新智元导读】" not in article.content_markdown
    assert "**【新智元导读】**这是一段导读文字，不应该成为五级标题。" in article.content_markdown


def test_parse_wechat_html_replaces_video_player_with_link_or_placeholder():
    html_with_src = """
    <html><body>
      <h1 id="activity-name">视频文章</h1>
      <div id="js_content">
        <p>视频前。</p>
        <span class="video_iframe rich_pages">
          已关注 Follow Replay Share Like Close
          <div class="js_mpvedio page_video_wrapper">
            <video src="https://mpvideo.qpic.cn/demo.mp4?token=1">Your browser does not support video tags</video>
            <a href="javascript:;">Play</a>
          </div>
          <div class="interact_video"><a href="javascript:;">Video Details</a></div>
        </span>
        <p>视频后。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html_with_src, "https://mp.weixin.qq.com/s/video")

    assert "[视频](https://mpvideo.qpic.cn/demo.mp4?token=1)" in article.content_markdown
    assert "Your browser does not support video tags" not in article.content_markdown
    assert "Play" not in article.content_markdown
    assert "Follow" not in article.content_markdown
    assert "Video Details" not in article.content_markdown

    html_without_src = html_with_src.replace(' src="https://mpvideo.qpic.cn/demo.mp4?token=1"', "")
    placeholder_article = parse_wechat_html(html_without_src, "https://mp.weixin.qq.com/s/video")

    assert "[视频] 原文包含视频，未能提取视频链接。" in placeholder_article.content_markdown


def test_parse_wechat_html_filters_decorative_images_by_default():
    html = """
    <html><body>
      <h1 id="activity-name">装饰图文章</h1>
      <div id="js_content">
        <p>正文前。</p>
        <img data-src="https://example.com/decor.png" class="rich_pages wxw-img wx_img_placeholder_mini"
             data-w="1080" data-ratio="0.851" style="width: 18px !important; height: auto;" />
        <img data-src="https://example.com/content.png" data-w="882" data-ratio="0.365" />
        <p>正文后。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/decor")

    assert "https://example.com/decor.png" not in article.content_markdown
    assert "https://example.com/content.png" in article.content_markdown
    assert [img.source_url for img in article.images] == ["https://example.com/content.png"]


def test_parse_wechat_html_simplifies_poster_template_heading_frames():
    html = """
    <html><body>
      <h1 id="activity-name">2026年小班秋季招生公告</h1>
      <a id="js_name">福州市马尾第三实验幼儿园</a>
      <div id="js_content">
        <section style="background-color: rgb(149, 140, 185);">
          <section>
            <img data-src="https://example.com/follow.png" data-w="329" data-ratio="0.10"
                 class="rich_pages wxw-img" />
          </section>
          <section>
            <img data-src="https://example.com/cover.png" data-w="683" data-ratio="0.58"
                 class="rich_pages wxw-img" />
          </section>
          <section>
            <img data-src="https://example.com/frame.png" data-w="655" data-ratio="0.265"
                 class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" />
          </section>
          <section style="grid-column-start: 1; grid-row-start: 1; display: flex;">
            <section style="font-size: 22px; color: rgb(149, 140, 185);">
              <p><span>计划招生数</span></p>
            </section>
          </section>
          <section>
            <p>小班：4个班，每班25人，共100人。</p>
          </section>
          <section>
            <img data-src="https://example.com/qr.png" data-w="500" data-ratio="1"
                 class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" />
          </section>
        </section>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/poster")

    assert "https://example.com/follow.png" not in article.content_markdown
    assert "https://example.com/frame.png" not in article.content_markdown
    assert "![Image](https://example.com/cover.png)" in article.content_markdown
    assert "![Image](https://example.com/qr.png)" in article.content_markdown
    assert "## 计划招生数" in article.content_markdown
    assert "小班：4个班，每班25人，共100人。" in article.content_markdown
    assert [img.source_url for img in article.images] == [
        "https://example.com/cover.png",
        "https://example.com/qr.png",
    ]


def test_parse_wechat_html_keeps_real_wide_placeholder_images():
    html = """
    <html><body>
      <h1 id="activity-name">真实横幅文章</h1>
      <div id="js_content">
        <p>正文前。</p>
        <img data-src="https://example.com/real-chart.png" data-w="800" data-ratio="0.25"
             class="rich_pages wxw-img js_img_placeholder wx_img_placeholder" />
        <p>这是图片说明。</p>
      </div>
    </body></html>
    """

    article = parse_wechat_html(html, "https://mp.weixin.qq.com/s/real-banner")

    assert "![Image](https://example.com/real-chart.png)" in article.content_markdown
    assert "这是图片说明。" in article.content_markdown
    assert [img.source_url for img in article.images] == ["https://example.com/real-chart.png"]
