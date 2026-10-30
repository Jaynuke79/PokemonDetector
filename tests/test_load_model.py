import pickle

import pytest
import torch
from PIL import Image

from lib.detector_core import get_transform, load_model, predict_image


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


def test_predict_image_accepts_a_path_or_a_file_object(
    tmp_path, stub_model, class_names
):
    path = tmp_path / "image.png"
    Image.new("RGB", (8, 8)).save(path)
    transform = get_transform()

    from_path = predict_image(path, stub_model, transform, "cpu", class_names)
    with path.open("rb") as stream:
        from_stream = predict_image(stream, stub_model, transform, "cpu", class_names)

    assert from_stream == from_path
