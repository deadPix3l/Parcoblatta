from pathlib import Path

from parcoblatta import QUERIES_PATH
from parcoblatta.cli.lint.config import LintConfig, load_lint_config


def test_lint_config_discovers_pyproject_upward_without_searching_siblings(tmp_path, monkeypatch):
    project = tmp_path / "stargate"
    nested = project / "src" / "jupiter"
    sibling = project / "other" / "pyproject.toml"
    nested.mkdir(parents=True)
    sibling.parent.mkdir()
    project.joinpath("pyproject.toml").write_text(
        "[tool.parcoblatta.lint]\ncode_dir = 'src'\n",
        encoding="utf-8",
    )
    sibling.write_text(
        "[tool.parcoblatta.lint]\ncode_dir = 'wrong'\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested)

    config = LintConfig()

    assert config.code_dir == [project / "src"]
    assert config.query_dir == [Path(QUERIES_PATH / "lint")]


def test_lint_config_discovers_pyproject_and_resolves_paths(tmp_path, monkeypatch):
    project = tmp_path / "stargate"
    nested = project / "src" / "jupiter"
    nested.mkdir(parents=True)
    project.joinpath("pyproject.toml").write_text(
        "[tool.parcoblatta.lint]\n"
        "code_dir = 'src'\n"
        "query_dir = 'queries/lint'\n"
        "select = 'no-eval'\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested)

    config = LintConfig()

    assert config.code_dir == [project / "src"]
    assert config.query_dir == [project / "queries" / "lint", Path(QUERIES_PATH / "lint")]
    assert config.select == ["no-eval"]


def test_lint_config_default_rules_false_disables_builtin_query_dir(tmp_path, monkeypatch):
    project = tmp_path / "stargate"
    nested = project / "src" / "jupiter"
    nested.mkdir(parents=True)
    project.joinpath("pyproject.toml").write_text(
        "[tool.parcoblatta.lint]\n"
        "query_dir = 'queries/lint'\n"
        "default_rules = false\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested)

    config = LintConfig()

    assert config.query_dir == [project / "queries" / "lint"]


def test_lint_config_explicit_missing_file_uses_defaults(tmp_path):
    config = load_lint_config(tmp_path / "missing.toml")

    assert config.code_dir == [Path(".")]
    assert config.query_dir == [Path(QUERIES_PATH / "lint")]


def test_lint_config_without_settings_uses_default_rules(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    config = LintConfig()

    assert config.query_dir == [Path(QUERIES_PATH / "lint")]
