#!/usr/bin/env node

const { spawnSync } = require("node:child_process");

const args = process.argv.slice(2);
const command = process.platform === "win32" ? "uvx.cmd" : "uvx";
// Equivalent command: uvx --from magicmd magicmd ...
const result = spawnSync(command, ["--from", "magicmd", "magicmd", ...args], {
  stdio: "inherit",
});

if (result.error) {
  if (result.error.code === "ENOENT") {
    console.error(
      "MagicMD npm wrapper requires uv. Install it from https://docs.astral.sh/uv/getting-started/installation/ or use: pipx install magicmd"
    );
    process.exit(127);
  }
  console.error(result.error.message);
  process.exit(1);
}

if (result.signal) {
  process.kill(process.pid, result.signal);
}

process.exit(result.status ?? 1);
