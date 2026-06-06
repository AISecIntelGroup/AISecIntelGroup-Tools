from pathlib import Path

from supply_chain_scanner.discover import discover_requirements


def test_discover_nested_requirements(tmp_path: Path) -> None:
    (tmp_path / "tools" / "a").mkdir(parents=True)
    (tmp_path / "tools" / "a" / "requirements.txt").write_text("requests>=2.0\n")
    (tmp_path / "tools" / "b" / "requirements.txt").parent.mkdir(parents=True)
    (tmp_path / "tools" / "b" / "requirements.txt").write_text("pytest>=8\n")

    found = discover_requirements(tmp_path)
    assert len(found) == 2
    assert found == sorted(found)


def test_discover_excludes_venv(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("ok\n")
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "requirements.txt").write_text("hidden\n")

    found = discover_requirements(tmp_path)
    assert len(found) == 1
    assert found[0].name == "requirements.txt"
    assert ".venv" not in str(found[0])


def test_discover_empty_root(tmp_path: Path) -> None:
    assert discover_requirements(tmp_path) == []
