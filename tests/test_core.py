import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_core_import_and_conversion_do_not_load_network_browser_or_cli():
    script = r"""
import importlib.abc
import socket
import sys

blocked = {"camoufox", "playwright", "httpx", "rich", "typer", "chardet"}
class BlockOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            if fullname.split(".")[0] == "chardet":
                raise ModuleNotFoundError(fullname)
            raise AssertionError("Core imported optional dependency: " + fullname)
sys.meta_path.insert(0, BlockOptional())
socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(AssertionError("network forbidden"))
from magicmd import parse_html, repair_markdown
article = parse_html('<title>核心测试</title><article><p>前文</p><img src="https://example.org/a.png"><p><strong>后文</strong></p></article>', 'https://example.org/article')
assert article.title == '核心测试'
assert article.content_markdown.index('前文') < article.content_markdown.index('![') < article.content_markdown.index('后文')
assert repair_markdown('**风险。**Anthropic') == '**风险**。Anthropic'
assert repair_markdown('`**风险。**Anthropic`') == '`**风险。**Anthropic`'
assert not blocked.intersection(sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_core_distribution_keeps_browser_and_cli_dependencies_optional():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    required = " ".join(project["dependencies"]).lower()
    assert all(
        name not in required for name in ("camoufox", "playwright", "typer", "rich", "httpx")
    )
    extras = project["optional-dependencies"]
    assert any("camoufox" in item for item in extras["browser"])
    assert any("typer" in item for item in extras["cli"])


def test_cli_entrypoint_explains_missing_click():
    script = r"""
import importlib.abc
import sys

class BlockClick(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "click":
            raise ModuleNotFoundError("No module named 'click'", name="click")
sys.meta_path.insert(0, BlockClick())
from magicmd.entrypoint import main
main()
"""
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "pip install 'magicmd[cli]'" in result.stderr
    assert "Traceback" not in result.stderr


def test_public_core_parse_rejects_unknown_platform():
    import magicmd

    parse_html = getattr(magicmd, "parse_html", None)
    assert callable(parse_html), "Missing public parse_html core API"
    try:
        parse_html("<article>正文</article>", "https://example.org", platform="unknown")
    except magicmd.UnsupportedPlatformError as error:
        assert error.stage == "detect"
    else:
        raise AssertionError("Unknown platform was accepted")
