import json
import re
from pathlib import Path


MANIFEST_PATH = Path("tests/fixtures/live_regression_manifest.json")
ALLOWED_PLATFORMS = {"wechat", "juejin", "csdn", "generic"}
ALLOWED_FETCH_MODES = {"camoufox", "http"}
ALLOWED_STATUSES = {"candidate", "converted", "needs_review", "blocked"}
ALLOWED_RESULTS = {"ok_without_warnings", "ok_with_warnings", "failed", "skipped"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_CHECKS = {
    "title",
    "author",
    "published_at",
    "markdown_body",
    "images",
    "links",
    "code_blocks",
    "metadata",
    "report",
}


def test_live_regression_manifest_exists_and_has_versioned_samples():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["version"] == 1
    assert manifest["purpose"]
    assert manifest["privacy_policy"]
    assert manifest["runbook"] == "docs/live-regression.md"
    assert manifest["schema"]["required_sample_fields"] == [
        "id",
        "platform",
        "url",
        "fetch_mode",
        "status",
        "focus",
        "checks",
        "review_notes",
    ]

    samples = manifest["samples"]
    assert len(samples) >= 3
    assert {sample["platform"] for sample in samples} >= {"wechat", "juejin", "csdn"}


def test_live_regression_samples_are_safe_and_actionable():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    seen_ids = set()

    for sample in manifest["samples"]:
        assert sample["id"] not in seen_ids
        seen_ids.add(sample["id"])
        assert sample["platform"] in ALLOWED_PLATFORMS
        assert sample["url"].startswith(
            (
                "https://mp.weixin.qq.com/",
                "https://juejin.cn/",
                "https://blog.csdn.net/",
                "https://",
            )
        )
        assert sample["fetch_mode"] in ALLOWED_FETCH_MODES
        assert sample["status"] in ALLOWED_STATUSES
        assert sample["focus"]
        assert set(sample["checks"]).issubset(REQUIRED_CHECKS)
        assert {"markdown_body", "metadata", "report"}.issubset(sample["checks"])
        assert sample["review_notes"]
        assert not sample.get("requires_login", False)
        assert not sample.get("contains_private_content", False)
        if "last_validated_at" in sample:
            assert DATE_PATTERN.match(sample["last_validated_at"])
        if "last_result" in sample:
            assert sample["last_result"] in ALLOWED_RESULTS
