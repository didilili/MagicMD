"""Check a built wheel in an isolated core-only, then CLI environment."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile


CORE_CHECK = r"""
import importlib.util
import sys
from magicmd import parse_html, repair_markdown, convert_article

optional = {"camoufox", "playwright", "httpx", "rich", "typer", "click", "chardet"}
assert all(importlib.util.find_spec(name) is None for name in optional)
article = parse_html('<title>Core</title><main><p>前文</p><img src="https://example.com/a.png"><p>后文</p></main>', 'https://example.com/post')
assert article.title == 'Core'
assert article.content_markdown.index('前文') < article.content_markdown.index('![') < article.content_markdown.index('后文')
assert repair_markdown('**风险。**Anthropic') == '**风险**。Anthropic'
assert repair_markdown('`**风险。**Anthropic`') == '`**风险。**Anthropic`'
assert not optional.intersection(sys.modules)
"""

SDK_CHECK = r"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from magicmd import convert_article

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write('<title>SDK smoke</title><article><p>中文正文</p></article>'.encode())
    def log_message(self, *args):
        pass

with HTTPServer(('127.0.0.1', 0), Handler) as server:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = convert_article(f'http://127.0.0.1:{server.server_port}/post', download_images=False)
        assert result.title == 'SDK smoke'
        assert '中文正文' in result.markdown
        assert result.package_dir is None
    finally:
        server.shutdown()
        thread.join()
"""


def main():
    wheel = Path(sys.argv[1]).resolve(strict=True)
    env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME"}}
    env["NO_PROXY"] = ",".join(filter(None, [env.get("NO_PROXY"), "127.0.0.1", "localhost"]))
    env["no_proxy"] = env["NO_PROXY"]
    with tempfile.TemporaryDirectory(prefix="magicmd-install-") as temporary:
        work = Path(temporary)
        venv = work / "venv"
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        cli = python.with_name("magicmd.exe" if os.name == "nt" else "magicmd")

        def run(*args, **kwargs):
            result = subprocess.run(args, cwd=work, env=env, text=True, timeout=180, **kwargs)
            if result.returncode:
                if result.stdout:
                    print(result.stdout, file=sys.stderr)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
                result.check_returncode()
            return result

        run("uv", "venv", "--python", sys.executable, str(venv))
        run("uv", "pip", "install", "--python", str(python), str(wheel))
        run(str(python), "-I", "-c", CORE_CHECK)
        missing = subprocess.run(
            [str(cli), "--version"], cwd=work, env=env, capture_output=True, text=True
        )
        assert missing.returncode != 0
        assert "magicmd[cli]" in missing.stderr and "Traceback" not in missing.stderr

        run("uv", "pip", "install", "--python", str(python), f"{wheel}[cli]")
        run("uv", "pip", "check", "--python", str(python))
        version = run(
            str(python),
            "-I",
            "-c",
            "from magicmd import __version__;print(__version__)",
            capture_output=True,
        ).stdout.strip()
        assert (
            run(str(cli), "--version", capture_output=True).stdout.strip() == f"MagicMD {version}"
        )
        run(str(cli), "--help", capture_output=True)
        run(str(python), "-I", "-c", SDK_CHECK)
        print("Installed wheel: core isolation, CLI and HTTP SDK passed.")


if __name__ == "__main__":
    main()
