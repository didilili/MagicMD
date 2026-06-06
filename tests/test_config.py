from pathlib import Path

from pagemd.config import load_config


def test_load_config_merges_toml_file(tmp_path: Path):
    config_path = tmp_path / ".pagemd.toml"
    config_path.write_text(
        """
        [output]
        directory = "articles"

        [images]
        download = false
        """,
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.output.directory == "articles"
    assert config.images.download is False
    assert config.images.directory == "images"

