from types import SimpleNamespace

from parcoblatta.cli.flow import app as flow_app


class FlowStub:
    rules = []

    def model_dump_json(self, indent=None):
        return "{}"


def test_run_uses_pyproject_log_level_for_explicit_yaml(monkeypatch, tmp_path):
    yaml_config = tmp_path / "flow.yml"
    yaml_config.write_text("code:\n  file: src\nrules: []\n", encoding="utf-8")
    calls = []

    monkeypatch.setattr(
        flow_app,
        "load_flow_settings",
        lambda file=None: SimpleNamespace(log_level="ERROR"),
    )
    monkeypatch.setattr(flow_app, "load_flow_config", lambda file=None: FlowStub())
    monkeypatch.setattr(
        flow_app.logging,
        "basicConfig",
        lambda **kwargs: calls.append(kwargs),
    )

    flow_app.run(yaml_config)

    assert calls[0]["level"] == "ERROR"


def test_run_cli_log_level_overrides_pyproject(monkeypatch, tmp_path):
    yaml_config = tmp_path / "flow.yml"
    yaml_config.write_text("code:\n  file: src\nrules: []\n", encoding="utf-8")
    calls = []

    monkeypatch.setattr(
        flow_app,
        "load_flow_settings",
        lambda file=None: SimpleNamespace(log_level="ERROR"),
    )
    monkeypatch.setattr(flow_app, "load_flow_config", lambda file=None: FlowStub())
    monkeypatch.setattr(
        flow_app.logging,
        "basicConfig",
        lambda **kwargs: calls.append(kwargs),
    )

    flow_app.run(yaml_config, log_level="DEBUG")

    assert calls[0]["level"] == "DEBUG"
