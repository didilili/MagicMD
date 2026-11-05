from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tomllib

import pytest
import yaml


def test_license_file_exists_for_mit_project():
    license_path = Path("LICENSE")

    assert license_path.exists()
    assert "MIT License" in license_path.read_text(encoding="utf-8")


def test_github_actions_ci_workflow_exists():
    workflow_path = Path(".github/workflows/ci.yml")

    assert workflow_path.exists()
    workflow = workflow_path.read_text(encoding="utf-8")
    assert "uv run pytest -q" in workflow
    assert "uv run ruff check ." in workflow
    assert "uv build" in workflow


def test_npm_wrapper_selects_shell_free_platform_executable():
    wrapper = Path("npm/magicmd/bin/magicmd.js").read_text(encoding="utf-8")

    assert "process.platform === 'win32' ? 'uvx.exe' : 'uvx'" in wrapper
    assert "uvx.cmd" not in wrapper
    assert "shell: true" not in wrapper


def test_ci_smokes_npm_wrapper_with_real_uvx_on_windows():
    workflow = yaml.safe_load(Path(".github/workflows/ci.yml").read_text(encoding="utf-8"))
    windows_job = workflow["jobs"].get("npm-wrapper-windows")

    assert windows_job is not None
    assert windows_job["runs-on"] == "windows-latest"
    steps = windows_job["steps"]
    checkout_index = next(
        (index for index, step in enumerate(steps) if step.get("uses") == "actions/checkout@v4"),
        None,
    )
    setup_uv_index = next(
        (index for index, step in enumerate(steps) if step.get("uses") == "astral-sh/setup-uv@v5"),
        None,
    )
    setup_node_entry = next(
        (
            (index, step)
            for index, step in enumerate(steps)
            if step.get("uses") == "actions/setup-node@v6"
        ),
        None,
    )
    version_entry = next(
        (
            (index, step)
            for index, step in enumerate(steps)
            if step.get("name") == "Use published npm wrapper version for Windows smoke"
        ),
        None,
    )
    smoke_entry = next(
        (
            (index, step)
            for index, step in enumerate(steps)
            if step.get("name") == "Smoke test npm wrapper on Windows"
        ),
        None,
    )

    assert checkout_index is not None
    assert setup_uv_index is not None
    assert setup_node_entry is not None
    assert version_entry is not None
    assert smoke_entry is not None
    setup_node_index, setup_node = setup_node_entry
    version_index, version_step = version_entry
    smoke_index, smoke_step = smoke_entry
    assert checkout_index < setup_uv_index < setup_node_index < version_index < smoke_index
    assert setup_node["with"]["node-version"] == 24
    assert version_step["shell"] == "pwsh"
    assert "npm/magicmd/package.json" in version_step["run"]
    assert '$package.version = "0.7.0"' in version_step["run"]
    assert "ConvertTo-Json" in version_step["run"]
    assert smoke_step["shell"] == "pwsh"
    assert "node npm/magicmd/bin/magicmd.js --version" in smoke_step["run"]
    assert "MagicMD 0.7.0" in smoke_step["run"]
    assert "$LASTEXITCODE" in smoke_step["run"]


def test_publish_workflow_supports_trusted_publishing_for_pypi_and_npm():
    workflow_path = Path(".github/workflows/publish.yml")

    assert workflow_path.exists()
    workflow = workflow_path.read_text(encoding="utf-8")

    assert "publish_pypi:" in workflow
    assert "publish_npm:" in workflow
    assert "environment: pypi" in workflow
    assert "environment: npm" in workflow
    assert "id-token: write" in workflow
    assert "actions/setup-node@v6" in workflow
    assert "package-manager-cache: false" in workflow
    assert "npm publish --registry=https://registry.npmjs.org --provenance" in workflow
    assert "working-directory: npm/magicmd" in workflow


def test_publish_npm_waits_for_matching_python_package_on_pypi():
    workflow = yaml.safe_load(Path(".github/workflows/publish.yml").read_text(encoding="utf-8"))
    publish_npm = workflow["jobs"]["publish-npm"]
    steps = publish_npm["steps"]

    setup_uv_index = next(
        (index for index, step in enumerate(steps) if step.get("uses") == "astral-sh/setup-uv@v5"),
        None,
    )
    guard_entry = next(
        (
            (index, step)
            for index, step in enumerate(steps)
            if step.get("name") == "Verify matching Python package is available on PyPI"
        ),
        None,
    )

    assert setup_uv_index is not None
    assert guard_entry is not None
    guard_index, guard = guard_entry
    npm_command_indexes = [
        index
        for index, step in enumerate(steps)
        if "npm pack" in step.get("run", "") or "npm publish" in step.get("run", "")
    ]
    assert setup_uv_index < guard_index
    assert npm_command_indexes
    assert all(guard_index < index for index in npm_command_indexes)
    assert guard["env"]["MAGICMD_VERSION"] == "${{ inputs.version }}"
    guard_script = guard["run"]
    assert (
        'uvx --refresh-package magicmd --from "magicmd==${MAGICMD_VERSION}" magicmd --version'
        in guard_script
    )
    assert "for attempt in $(seq 1 12)" in guard_script
    assert "sleep 10" in guard_script
    assert "matching PyPI version must be published before npm" in guard_script
    assert "exit 1" in guard_script


def test_project_metadata_uses_magicmd_name_and_cli():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["name"] == "magicmd"
    assert metadata["project"]["scripts"] == {"magicmd": "magicmd.entrypoint:main"}
    assert metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["src/magicmd"]


def test_project_metadata_constrains_playwright_for_camoufox():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert "playwright>=1.60,<1.61" in metadata["project"]["optional-dependencies"]["browser"]


def test_npm_wrapper_metadata_matches_python_package():
    python_metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    npm_package = json.loads(Path("npm/magicmd/package.json").read_text(encoding="utf-8"))
    readme = Path("npm/magicmd/README.md").read_text(encoding="utf-8")

    assert npm_package["name"] == "magicmd"
    assert npm_package["version"] == python_metadata["project"]["version"]
    assert npm_package["bin"] == {"magicmd": "bin/magicmd.js"}
    assert npm_package["private"] is False
    expected_command = f'uvx --from "magicmd[cli,browser]=={npm_package["version"]}" magicmd'
    assert expected_command in readme


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="real uvx.exe launcher is covered by the npm-wrapper-windows GitHub Actions smoke job",
)
def test_npm_wrapper_forwards_same_version_python_package(tmp_path):
    node = shutil.which("node")
    assert node is not None
    npm_package = json.loads(Path("npm/magicmd/package.json").read_text(encoding="utf-8"))
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    captured_argv = tmp_path / "uvx-argv.json"
    fake_uvx = fake_bin / "uvx"
    fake_uvx.write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "import json",
                "import os",
                "from pathlib import Path",
                "import sys",
                "",
                'Path(os.environ["MAGICMD_TEST_UVX_ARGV"]).write_text(',
                '    json.dumps(sys.argv[1:]), encoding="utf-8"',
                ")",
            ]
        ),
        encoding="utf-8",
    )

    fake_uvx.chmod(0o755)

    env = {
        "PATH": str(fake_bin),
        "MAGICMD_TEST_UVX_ARGV": str(captured_argv),
    }
    forwarded_args = ["doctor", "--json"]
    result = subprocess.run(
        [node, str(Path("npm/magicmd/bin/magicmd.js").resolve()), *forwarded_args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(captured_argv.read_text(encoding="utf-8")) == [
        "--from",
        f"magicmd[cli,browser]=={npm_package['version']}",
        "magicmd",
        *forwarded_args,
    ]


def test_npm_wrapper_explains_missing_uvx(tmp_path):
    node = shutil.which("node")
    assert node is not None
    npm_package = json.loads(Path("npm/magicmd/package.json").read_text(encoding="utf-8"))
    env = os.environ.copy()
    env["PATH"] = str(tmp_path)

    result = subprocess.run(
        [node, "npm/magicmd/bin/magicmd.js", "--version"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 127
    assert "MagicMD npm package needs uv" in result.stderr
    assert f'uvx --from "magicmd[cli,browser]=={npm_package["version"]}" magicmd' in result.stderr
    assert "curl -LsSf https://astral.sh/uv/install.sh | sh" in result.stderr
    assert "powershell -ExecutionPolicy ByPass" in result.stderr
    assert 'uv tool install "magicmd[cli,browser]"' in result.stderr
    assert 'pipx install "magicmd[cli,browser]"' in result.stderr


def test_publishable_skill_exists():
    skill_path = Path("skills/magicmd/SKILL.md")
    openai_yaml_path = Path("skills/magicmd/agents/openai.yaml")

    assert skill_path.exists()
    assert openai_yaml_path.exists()

    skill = skill_path.read_text(encoding="utf-8")
    openai_agent = yaml.safe_load(openai_yaml_path.read_text(encoding="utf-8"))

    assert "name: magicmd" in skill
    assert 'uvx --from "magicmd==0.7.1" magicmd' in skill
    assert "extraction-report.json" in skill
    assert "Do not use it to bypass login" in skill
    assert openai_agent["interface"]["display_name"] == "MagicMD"
    assert openai_agent["policy"]["allow_implicit_invocation"] is True


def test_publish_workflow_documented_on_website():
    quick_start = Path("website/quick-start.md").read_text(encoding="utf-8")
    config_doc = Path("website/config.md").read_text(encoding="utf-8")
    publish_doc = Path("website/publish-github.md").read_text(encoding="utf-8")
    english_quick_start = Path("website/en/quick-start.md").read_text(encoding="utf-8")
    english_config_doc = Path("website/en/config.md").read_text(encoding="utf-8")
    english_publish_doc = Path("website/en/publish-github.md").read_text(encoding="utf-8")

    assert "magicmd publish github" in quick_start
    assert "[publish.github]" in config_doc
    assert "推荐路径：先配置，再发布" in publish_doc
    assert 'magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run' in publish_doc
    assert "看懂 dry-run 输出" in publish_doc
    assert "debug.html" in publish_doc
    assert "target_dir" in publish_doc
    assert "创建一个内容仓库" in publish_doc
    assert "生成 GitHub token" in publish_doc
    assert "Contents permission" in publish_doc
    assert 'target_dir = "content/posts/{date}-{slug}"' in publish_doc
    assert "GITHUB_TOKEN=ghp_xxx" in publish_doc
    assert ".env" in publish_doc
    assert "magicmd publish github" in english_quick_start
    assert "[publish.github]" in english_config_doc
    assert "Recommended path: configure first, publish later" in english_publish_doc
    assert 'magicmd publish github "https://mp.weixin.qq.com/s/example" --dry-run' in (
        english_publish_doc
    )
    assert "Read the dry-run output" in english_publish_doc
    assert "debug.html" in english_publish_doc
    assert "target_dir" in english_publish_doc
    assert "Create a content repository" in english_publish_doc
    assert "Create a GitHub token" in english_publish_doc
    assert "Contents permission" in english_publish_doc
    assert 'target_dir = "content/posts/{date}-{slug}"' in english_publish_doc
    assert "GITHUB_TOKEN=ghp_xxx" in english_publish_doc
    assert ".env" in english_publish_doc


def test_studio_console_documented_on_website():
    quick_start = Path("website/quick-start.md").read_text(encoding="utf-8")
    studio_doc = Path("website/studio.md").read_text(encoding="utf-8")
    english_quick_start = Path("website/en/quick-start.md").read_text(encoding="utf-8")
    english_studio_doc = Path("website/en/studio.md").read_text(encoding="utf-8")
    vitepress_config = Path("website/.vitepress/config.ts").read_text(encoding="utf-8")
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    wheel_assets = metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]

    assert "magicmd studio" in quick_start
    assert "[MagicMD Studio](/studio)" in quick_start
    assert "预览发布计划" in studio_doc
    assert "http://127.0.0.1:8765" in studio_doc
    assert "magicmd studio" in english_quick_start
    assert "[MagicMD Studio](/en/studio)" in english_quick_start
    assert "Preview publish plan" in english_studio_doc
    assert "http://127.0.0.1:8765" in english_studio_doc
    assert "{ text: 'Studio', link: '/studio' }" in vitepress_config
    assert "{ text: 'Studio', link: '/en/studio' }" in vitepress_config
    assert wheel_assets["src/magicmd/studio/index.html"] == "magicmd/studio/index.html"
    assert wheel_assets["src/magicmd/studio/studio.css"] == "magicmd/studio/studio.css"
    assert wheel_assets["src/magicmd/studio/studio.js"] == "magicmd/studio/studio.js"
