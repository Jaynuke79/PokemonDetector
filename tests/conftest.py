import json
import os
import tempfile
from pathlib import Path

import pytest
import torch
from torch import nn

CLASS_NAMES = ["bulbasaur", "charmander", "squirtle"]


_session_dir = tempfile.TemporaryDirectory(prefix="pokemondetector-tests-")
_session_root = Path(_session_dir.name).resolve()
_real_torch_load = torch.load


def _torch_load_from_session_dir_only(f, *args, **kwargs):
    if not Path(f).resolve().is_relative_to(_session_root):
        pytest.fail(
            f"Tests must not load real model weights, but torch.load got {f}; "
            "use the stub_weights fixture.",
            pytrace=False,
        )
    return _real_torch_load(f, *args, **kwargs)


# webapp.app loads the model at import time from cwd-relative models/ paths, and
# its blanket `except Exception` would swallow an ordinary error. pytest.fail
# raises a BaseException, so loading weights from outside the session directory
# fails the run, and the empty cwd keeps the import from finding real weights in
# the first place.
torch.load = _torch_load_from_session_dir_only
os.chdir(_session_root)


class StubClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.head = nn.Linear(3, num_classes)

    def forward(self, images):
        return self.head(images.mean(dim=(2, 3)))


@pytest.fixture
def class_names():
    return list(CLASS_NAMES)


@pytest.fixture
def class_names_path(tmp_path, class_names):
    path = tmp_path / "class_names.json"
    path.write_text(json.dumps(class_names))
    return path


@pytest.fixture
def stub_model(class_names):
    return StubClassifier(len(class_names)).eval()


@pytest.fixture
def stub_architecture(monkeypatch, stub_model):
    """Make load_model build the stub rather than an 88M-parameter ConvNeXt."""
    monkeypatch.setattr(
        "lib.detector_core.timm.create_model", lambda *_a, **_k: stub_model
    )


@pytest.fixture
def weights_dir():
    with tempfile.TemporaryDirectory(dir=_session_root) as path:
        yield Path(path)


@pytest.fixture
def stub_weights(weights_dir, stub_model):
    path = weights_dir / "stub.pth"
    torch.save(stub_model.state_dict(), path)
    return path


@pytest.fixture
def corrupt_weights(weights_dir):
    path = weights_dir / "corrupt.pth"
    path.write_bytes(b"not a checkpoint")
    return path


@pytest.fixture
def webapp_module():
    import webapp.app

    return webapp.app


@pytest.fixture
def client(webapp_module):
    return webapp_module.app.test_client()
