from pathlib import Path

from parcoblatta.cli.flow.config import FlowConfig, load_flow_config, load_flow_settings


def test_flow_settings_load_from_pyproject_and_resolve_paths(tmp_path, monkeypatch):
    project = tmp_path / "stargate"
    nested = project / "src" / "jupiter"
    nested.mkdir(parents=True)
    project.joinpath("pyproject.toml").write_text(
        "[tool.parcoblatta.flow]\n"
        "config_dir = 'flows'\n"
        "default = 'review.yml'\n"
        "code_dir = 'src'\n"
        "query_dir = 'queries'\n"
        "template_dir = 'prompts'\n"
        "output_dir = '.parcoblatta'\n"
        "exclude = ['generated']\n"
        "log_level = 'DEBUG'\n"
        "[tool.parcoblatta.flow.kafka]\n"
        "bootstrap_servers = ['kafka:9092']\n"
        "client_id = 'stargate'\n"
        "topic_prefix = 'stargate.dev'\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested)

    config = FlowConfig()

    assert config.config_dir == [project / "flows"]
    assert config.default == Path("review.yml")
    assert config.default_config_file() == project / "flows" / "review.yml"
    assert config.code_dir == [project / "src"]
    assert config.query_dir == [project / "queries"]
    assert config.template_dir == [project / "prompts"]
    assert config.output_dir == project / ".parcoblatta"
    assert config.exclude == ["generated"]
    assert config.log_level == "DEBUG"
    assert config.kafka.bootstrap_servers == ["kafka:9092"]
    assert config.kafka.client_id == "stargate"
    assert config.kafka.topic_prefix == "stargate.dev"


def test_load_flow_config_uses_default_yaml_from_flow_settings(tmp_path, monkeypatch):
    project = tmp_path / "stargate"
    flow_dir = project / "flows"
    nested = project / "src" / "jupiter"
    nested.mkdir(parents=True)
    flow_dir.mkdir(parents=True)
    project.joinpath("pyproject.toml").write_text(
        "[tool.parcoblatta.flow]\n"
        "config_dir = 'flows'\n"
        "default = 'review.yml'\n",
        encoding="utf-8",
    )
    flow_dir.joinpath("review.yml").write_text(
        "code:\n"
        "  file: src\n"
        "rules:\n"
        "  - query:\n"
        "      text: '(function_definition) @function'\n"
        "    output:\n"
        "      stdout: true\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested)

    flow = load_flow_config()

    assert flow.code.file == [project / "src"]
    assert flow.rules[0].output.stdout is True


def test_load_flow_config_uses_query_dir_for_default_yaml(tmp_path, monkeypatch):
    project = tmp_path / "stargate"
    flow_dir = project / "flows"
    query_dir = project / "queries" / "flow"
    nested = project / "src" / "jupiter"
    nested.mkdir(parents=True)
    flow_dir.mkdir(parents=True)
    query_dir.mkdir(parents=True)
    project.joinpath("pyproject.toml").write_text(
        "[tool.parcoblatta.flow]\n"
        "config_dir = 'flows'\n"
        "default = 'review.yml'\n"
        "query_dir = 'queries/flow'\n",
        encoding="utf-8",
    )
    flow_dir.joinpath("review.yml").write_text(
        "code:\n"
        "  file: src\n"
        "rules:\n"
        "  - query:\n"
        "      file: functions.scm\n"
        "    output:\n"
        "      stdout: true\n",
        encoding="utf-8",
    )
    query_dir.joinpath("functions.scm").write_text("(function_definition) @function\n")

    monkeypatch.chdir(nested)

    flow = load_flow_config()

    assert flow.rules[0].query.file == [query_dir / "functions.scm"]


def test_load_flow_config_applies_kafka_defaults(tmp_path, monkeypatch):
    project = tmp_path / "stargate"
    flow_dir = project / "flows"
    nested = project / "src" / "jupiter"
    nested.mkdir(parents=True)
    flow_dir.mkdir(parents=True)
    project.joinpath("pyproject.toml").write_text(
        "[tool.parcoblatta.flow]\n"
        "config_dir = 'flows'\n"
        "default = 'review.yml'\n"
        "[tool.parcoblatta.flow.kafka]\n"
        "bootstrap_servers = ['kafka:9092']\n"
        "client_id = 'stargate'\n",
        encoding="utf-8",
    )
    flow_dir.joinpath("review.yml").write_text(
        "code:\n"
        "  file: src\n"
        "rules:\n"
        "  - query:\n"
        "      text: '(function_definition) @function'\n"
        "    output:\n"
        "      topic: parcoblatta.matches\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested)

    flow = load_flow_config()

    assert flow.rules[0].output.kafka.bootstrap_servers == ["kafka:9092"]
    assert flow.rules[0].output.kafka.client_id == "stargate"


def test_load_flow_config_applies_topic_prefix(tmp_path, monkeypatch):
    project = tmp_path / "stargate"
    flow_dir = project / "flows"
    nested = project / "src" / "jupiter"
    nested.mkdir(parents=True)
    flow_dir.mkdir(parents=True)
    project.joinpath("pyproject.toml").write_text(
        "[tool.parcoblatta.flow]\n"
        "config_dir = 'flows'\n"
        "default = 'review.yml'\n"
        "[tool.parcoblatta.flow.kafka]\n"
        "topic_prefix = 'stargate.dev'\n",
        encoding="utf-8",
    )
    flow_dir.joinpath("review.yml").write_text(
        "code:\n"
        "  file: src\n"
        "rules:\n"
        "  - query:\n"
        "      text: '(function_definition) @function'\n"
        "    output:\n"
        "      topic:\n"
        "        - matches\n"
        "        - stargate.dev.prompts\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested)

    flow = load_flow_config()

    assert flow.rules[0].output.topic == ["stargate.dev.matches", "stargate.dev.prompts"]


def test_load_flow_config_keeps_yaml_support(tmp_path):
    config = tmp_path / "flow.yml"
    config.write_text(
        "code:\n"
        "  file: src\n"
        "rules:\n"
        "  - query:\n"
        "      text: '(function_definition) @function'\n"
        "    output:\n"
        "      stdout: true\n",
        encoding="utf-8",
    )

    flow = load_flow_config(config)

    assert flow.code.file[0].as_posix() == "src"
    assert flow.rules[0].output.stdout is True


def test_load_flow_settings_explicit_missing_file_uses_defaults(tmp_path):
    config = load_flow_settings(tmp_path / "missing.toml")

    assert config.config_dir == [Path("flows")]
    assert config.default is None
