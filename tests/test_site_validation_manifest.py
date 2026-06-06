import json
from pathlib import Path


def test_site_validation_manifest_records_current_platform_baseline():
    manifest_path = Path("tests/fixtures/site_validation_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["version"] == 1
    assert manifest["generated_from"] == "output/juejin-homepage-003-default-fixed/batch-report.md"

    platforms = {item["platform"] for item in manifest["articles"]}
    assert {"wechat", "csdn", "juejin", "generic"}.issubset(set(manifest["platform_status"]))
    assert {"csdn", "juejin"}.issubset(platforms)

    csdn_items = [item for item in manifest["articles"] if item["platform"] == "csdn"]
    juejin_items = [item for item in manifest["articles"] if item["platform"] == "juejin"]

    assert csdn_items
    assert all(item["fetch_mode"] == "camoufox" for item in csdn_items)
    assert all(item["status"] == "converted_with_quality_warnings" for item in csdn_items)
    assert len(juejin_items) >= 5
    assert all(item["fetch_mode"] == "camoufox" for item in juejin_items)
    assert all(item["status"] == "converted" for item in juejin_items)
    assert all(item["notes"] for item in manifest["articles"])
