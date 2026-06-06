import json
from pathlib import Path


def test_wechat_regression_manifest_has_unique_urls_and_issue_tags():
    manifest_path = Path("tests/fixtures/wechat_regression_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    urls = [item["url"] for item in manifest["articles"]]

    assert manifest["version"] == 1
    assert len(urls) >= 10
    assert len(urls) == len(set(urls))
    assert all(item["platform"] == "wechat" for item in manifest["articles"])
    assert all(item["issue_tags"] for item in manifest["articles"])
