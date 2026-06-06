from pathlib import Path
import tomllib


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


def test_project_metadata_uses_magicmd_name_and_cli():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["name"] == "magicmd"
    assert metadata["project"]["scripts"] == {"magicmd": "magicmd.cli:entrypoint"}
    assert metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["src/magicmd"]
