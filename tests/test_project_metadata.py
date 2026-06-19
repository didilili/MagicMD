from pathlib import Path
import json
import shutil
import subprocess
import tomllib

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


def test_project_metadata_uses_magicmd_name_and_cli():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["name"] == "magicmd"
    assert metadata["project"]["scripts"] == {"magicmd": "magicmd.cli:entrypoint"}
    assert metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["src/magicmd"]


def test_npm_wrapper_metadata_matches_python_package():
    python_metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    npm_package = json.loads(Path("npm/magicmd/package.json").read_text(encoding="utf-8"))
    wrapper = Path("npm/magicmd/bin/magicmd.js").read_text(encoding="utf-8")
    readme = Path("npm/magicmd/README.md").read_text(encoding="utf-8")

    assert npm_package["name"] == "magicmd"
    assert npm_package["version"] == python_metadata["project"]["version"]
    assert npm_package["bin"] == {"magicmd": "bin/magicmd.js"}
    assert npm_package["private"] is False
    assert "uvx --from magicmd magicmd" in wrapper
    assert "uvx --from magicmd magicmd" in readme


def test_npm_wrapper_explains_missing_uvx():
    node = shutil.which("node")
    assert node is not None

    result = subprocess.run(
        [node, "npm/magicmd/bin/magicmd.js", "--version"],
        check=False,
        capture_output=True,
        text=True,
        env={"PATH": "/tmp/magicmd-no-uvx"},
    )

    assert result.returncode == 127
    assert "MagicMD npm package needs uv" in result.stderr
    assert "curl -LsSf https://astral.sh/uv/install.sh | sh" in result.stderr
    assert "powershell -ExecutionPolicy ByPass" in result.stderr
    assert "uv tool install magicmd" in result.stderr
    assert "pipx install magicmd" in result.stderr


def test_publishable_skill_exists():
    skill_path = Path("skills/magicmd/SKILL.md")
    openai_yaml_path = Path("skills/magicmd/agents/openai.yaml")

    assert skill_path.exists()
    assert openai_yaml_path.exists()

    skill = skill_path.read_text(encoding="utf-8")
    openai_agent = yaml.safe_load(openai_yaml_path.read_text(encoding="utf-8"))

    assert "name: magicmd" in skill
    assert "uvx --from magicmd magicmd" in skill
    assert "extraction-report.json" in skill
    assert "Do not use it to bypass login" in skill
    assert openai_agent["interface"]["display_name"] == "MagicMD"
    assert openai_agent["policy"]["allow_implicit_invocation"] is True


def test_publish_workflow_documented_on_website():
    quick_start = Path("website/quick-start.md").read_text(encoding="utf-8")
    config_doc = Path("website/config.md").read_text(encoding="utf-8")
    english_quick_start = Path("website/en/quick-start.md").read_text(encoding="utf-8")
    english_config_doc = Path("website/en/config.md").read_text(encoding="utf-8")

    assert "magicmd publish github" in quick_start
    assert "[publish.github]" in config_doc
    assert "magicmd publish github" in english_quick_start
    assert "[publish.github]" in english_config_doc
