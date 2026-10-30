import json


def test_initialize_model_reports_failure_when_load_model_raises(
    webapp_module, monkeypatch, tmp_path, capsys
):
    models = tmp_path / "models"
    models.mkdir()
    (models / "class_names.json").write_text(json.dumps(["a", "b", "c"]))
    (models / "best_model_fold1.pth").write_bytes(b"")
    monkeypatch.chdir(tmp_path)
    for name in ("class_names", "model", "transform", "device"):
        monkeypatch.setattr(webapp_module, name, None)

    def raise_load_error(*_args):
        raise RuntimeError("bad checkpoint")

    monkeypatch.setattr(webapp_module, "load_model", raise_load_error)

    assert webapp_module.initialize_model() is False
    assert webapp_module.model is None
    assert "bad checkpoint" in capsys.readouterr().out
