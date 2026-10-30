import pytest

import lib.detector_core


def test_real_weight_loading_is_forbidden():
    with pytest.raises(pytest.fail.Exception):
        lib.detector_core.load_model("convnext_base", 3, "models/x.pth", "cpu")


def test_webapp_import_does_not_load_a_model(webapp_module):
    assert webapp_module.model is None


def test_health_returns_503_when_model_is_not_loaded(
    webapp_module, client, monkeypatch
):
    monkeypatch.setattr(webapp_module, "model", None)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unhealthy", "model_loaded": False}


def test_health_returns_200_when_model_is_loaded(
    webapp_module, client, monkeypatch, stub_model
):
    monkeypatch.setattr(webapp_module, "model", stub_model)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy", "model_loaded": True}
