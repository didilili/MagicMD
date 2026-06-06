from urllib.parse import urlparse


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "mp.weixin.qq.com" in host:
        return "wechat"
    if "juejin.cn" in host:
        return "juejin"
    if "csdn.net" in host:
        return "csdn"
    return "generic"

