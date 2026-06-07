# MagicMD npm Wrapper

This package is a thin npm wrapper for the Python MagicMD CLI.

It does not reimplement article parsing in JavaScript. It forwards commands to the PyPI package with:

```bash
uvx --from magicmd magicmd
```

## Requirements

- Node.js 18+
- `uv` available on `PATH`

## Usage

After the npm package is published:

```bash
npm install -g magicmd
magicmd --version
magicmd batch urls.txt -o output/
```

Until then, install MagicMD directly from PyPI:

```bash
uv tool install magicmd
magicmd doctor
```

## Why This Wrapper Exists

MagicMD's core implementation lives in Python so that the CLI, PyPI package, and Agent Skill use the same parsing and conversion code. The npm package is only an installation convenience for users who expect a global `magicmd` command from npm.
