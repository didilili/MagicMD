#!/usr/bin/env node

const { spawnSync } = require('node:child_process');
const { version: packageVersion } = require('../package.json');

const args = process.argv.slice(2);
const command = process.platform === 'win32' ? 'uvx.exe' : 'uvx';
const pythonPackage = `magicmd==${packageVersion}`;
// Equivalent command: uvx --from "magicmd==<npm package version>" magicmd ...
const result = spawnSync(command, ['--from', pythonPackage, 'magicmd', ...args], {
  stdio: 'inherit'
});

if (result.error) {
  if (result.error.code === 'ENOENT') {
    console.error(`MagicMD npm package needs uv to run the Python CLI.

The npm package is a thin wrapper around:
uvx --from "${pythonPackage}" magicmd

Install uv:
macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

Or install MagicMD directly:
uv tool install magicmd
pipx install magicmd`);
    process.exit(127);
  }
  console.error(result.error.message);
  process.exit(1);
}

if (result.signal) {
  process.kill(process.pid, result.signal);
}

process.exit(result.status ?? 1);
