import pytest

from pagemd.detect import detect_platform


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://mp.weixin.qq.com/s/abc", "wechat"),
        ("https://juejin.cn/post/123", "juejin"),
        ("https://blog.csdn.net/user/article/details/1", "csdn"),
        ("https://blog.example.com/a", "generic"),
    ],
)
def test_detect_platform(url, expected):
    assert detect_platform(url) == expected

