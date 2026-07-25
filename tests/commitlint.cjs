const { spawnSync } = require('node:child_process');

const commitlintCli = require.resolve('@commitlint/cli/cli.js');

const cases = [
  {
    name: '接受中文主题和中文正文',
    message: 'fix: 修复提交信息校验\n\n补充中文正文，说明本次修改的原因和影响范围。\n',
    accepted: true
  },
  {
    name: '拒绝英文主题',
    message: 'fix: enforce commit message rules\n\n补充中文正文，说明本次修改的原因和影响范围。\n',
    accepted: false
  },
  {
    name: '拒绝空正文',
    message: 'fix: 修复提交信息校验\n',
    accepted: false
  },
  {
    name: '拒绝只有英文的正文',
    message: 'fix: 修复提交信息校验\n\nExplain the reason and impact of this change.\n',
    accepted: false
  }
];

let failed = false;

for (const testCase of cases) {
  const result = spawnSync(process.execPath, [commitlintCli], {
    cwd: process.cwd(),
    input: testCase.message,
    encoding: 'utf8'
  });
  const accepted = result.status === 0;

  if (accepted !== testCase.accepted) {
    failed = true;
    console.error(`✗ ${testCase.name}`);
    console.error(result.stdout || result.stderr || 'commitlint 未返回错误信息');
  } else {
    console.log(`✓ ${testCase.name}`);
  }
}

if (failed) {
  process.exitCode = 1;
}
