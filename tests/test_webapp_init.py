import json

import pytest


@pytest.fixture
def reset_model_state(webapp_module, monkeypatch):
    for name in ("class_names", "model", "transform", "device"):
        monkeypatch.setattr(webapp_module, name, None)


@pytest.fixture
def cwd_with_decoy_models(monkeypatch, tmp_path):
    cwd = tmp_path / "elsewhere"
    (cwd / "models").mkdir(parents=True)
    (cwd / "models" / "class_names.json").write_text("not json")
    (cwd / "models" / "best_model_fold1.pth").write_bytes(b"not a checkpoint")
    monkeypatch.chdir(cwd)


@pytest.fixture
def models_dir(monkeypatch, weights_dir, stub_weights, class_names_path):
    stub_weights.rename(weights_dir / "best_model_fold1.pth")
    class_names_path.rename(weights_dir / "class_names.json")
    monkeypatch.setenv("POKE_MODELS_DIR", str(weights_dir))
    return weights_dir


@pytest.mark.usefixtures(
    "reset_model_state", "stub_architecture", "cwd_with_decoy_models", "models_dir"
)
def test_initialize_model_finds_models_regardless_of_cwd(
    webapp_module, client, stub_model
):
    assert webapp_module.initialize_model() is True
    assert webapp_module.model is stub_model
    assert client.get("/health").status_code == 200


@pytest.mark.usefixtures("reset_model_state", "cwd_with_decoy_models")
def test_initialize_model_names_the_missing_class_names_file(
    webapp_module, monkeypatch, tmp_path, capsys
):
    monkeypatch.setenv("POKE_MODELS_DIR", str(tmp_path))

    assert webapp_module.initialize_model() is False
    assert str(tmp_path / "class_names.json") in capsys.readouterr().out


@pytest.mark.usefixtures("reset_model_state", "cwd_with_decoy_models")
def test_initialize_model_names_the_missing_weights_file(
    webapp_module, monkeypatch, tmp_path, capsys
):
    (tmp_path / "class_names.json").write_text(json.dumps(["a", "b", "c"]))
    monkeypatch.setenv("POKE_MODELS_DIR", str(tmp_path))

    assert webapp_module.initialize_model() is False
    assert webapp_module.model is None
    assert str(tmp_path / "best_model_fold1.pth") in capsys.readouterr().out


@pytest.mark.usefixtures("reset_model_state", "cwd_with_decoy_models")
def test_initialize_model_reports_failure_when_load_model_raises(
    webapp_module, monkeypatch, tmp_path, capsys
):
    (tmp_path / "class_names.json").write_text(json.dumps(["a", "b", "c"]))
    (tmp_path / "best_model_fold1.pth").write_bytes(b"")
    monkeypatch.setenv("POKE_MODELS_DIR", str(tmp_path))

    def raise_load_error(*_args):
        raise RuntimeError("bad checkpoint")

    monkeypatch.setattr(webapp_module, "load_model", raise_load_error)

    assert webapp_module.initialize_model() is False
    assert webapp_module.model is None
    assert "bad checkpoint" in capsys.readouterr().out
