import json
import os
import tempfile

import pytest
import torch
from torch import nn

import lib.detector_core

CLASS_NAMES = ["bulbasaur", "charmander", "squirtle"]


def _forbid_real_weight_loading(*_args, **_kwargs):
    pytest.fail(
        "Tests must not load real model weights; use the stub_model fixture.",
        pytrace=False,
    )


# webapp.app loads the model at import time from cwd-relative models/ paths, and
# its blanket `except Exception` would swallow an ordinary error. pytest.fail
# raises a BaseException, so any attempt to load weights fails the run, and the
# empty cwd keeps the import from finding real weights in the first place.
lib.detector_core.load_model = _forbid_real_weight_loading
torch.load = _forbid_real_weight_loading
_empty_cwd = tempfile.TemporaryDirectory(prefix="pokemondetector-tests-")
os.chdir(_empty_cwd.name)


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
def webapp_module():
    import webapp.app

    return webapp.app


@pytest.fixture
def client(webapp_module):
    return webapp_module.app.test_client()
