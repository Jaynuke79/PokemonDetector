import pickle

import pytest
import torch

from lib.detector_core import load_model


def test_torch_load_refuses_paths_outside_the_session_dir(tmp_path):
    outside = tmp_path / "best_model_fold1.pth"
    outside.write_bytes(b"")

    with pytest.raises(pytest.fail.Exception, match="must not load real model weights"):
        torch.load(outside)


@pytest.mark.usefixtures("stub_architecture")
def test_load_model_returns_model_in_eval_mode(stub_weights, stub_model):
    stub_model.train()

    loaded = load_model("stub", 3, stub_weights, "cpu")

    assert loaded is stub_model
    assert not loaded.training


@pytest.mark.usefixtures("stub_architecture")
def test_load_model_raises_on_missing_weights(weights_dir):
    with pytest.raises(FileNotFoundError):
        load_model("stub", 3, weights_dir / "missing.pth", "cpu")


@pytest.mark.usefixtures("stub_architecture")
def test_load_model_raises_on_corrupt_weights(corrupt_weights):
    with pytest.raises(pickle.UnpicklingError):
        load_model("stub", 3, corrupt_weights, "cpu")
