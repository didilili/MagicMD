# MagicMD npm Wrapper

This package is a thin npm wrapper for the Python MagicMD CLI.

It does not reimplement article parsing in JavaScript. The wrapper reads its npm package version and requests the same Python package version, so `magicmd@0.7.9` runs `magicmd==0.7.9` with:

```bash
uvx --from "magicmd==0.7.9" magicmd
```

On Windows, the wrapper launches `uvx.exe` directly; on macOS and Linux, it launches `uvx`. The wrapper passes arguments without enabling shell execution.

## Requirements

- Node.js 18+
- `uv` available on `PATH`

If `uvx` is missing, install `uv` first:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Usage

```bash
npm install -g magicmd
magicmd --version
magicmd batch urls.txt -o output/
```

You can also install MagicMD directly from PyPI:

```bash
uv tool install magicmd
pipx install magicmd
magicmd doctor
```

## Why This Wrapper Exists

MagicMD's core implementation lives in Python so that the CLI, PyPI package, and Agent Skill use the same parsing and conversion code. The npm package is only an installation convenience for users who expect a global `magicmd` command from npm.
