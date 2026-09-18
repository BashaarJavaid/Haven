import tomllib
from importlib.metadata import metadata
from pathlib import Path

import hirz


def test_package_import_and_metadata() -> None:
    project_file = Path(__file__).resolve().parents[2] / "pyproject.toml"
    project = tomllib.loads(project_file.read_text())["project"]
    installed = metadata("hirz")
    assert hirz.__name__ == installed["Name"] == project["name"]
    assert installed["Version"] == project["version"]
