import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("package", ["torch", "torchvision"])
def test_dockerfile_cpu_pin_matches_requirements(package):
    dockerfile = (REPO_ROOT / "deployment" / "Dockerfile").read_text()
    requirements = (REPO_ROOT / "requirements.txt").read_text()

    cpu_pin = re.search(rf"\b{package}==(\S+)\+cpu\b", dockerfile)

    assert cpu_pin, f"no {package}==X+cpu pin in deployment/Dockerfile"
    assert re.findall(rf"^{package}==([^\s;]+)", requirements, re.MULTILINE) == [
        cpu_pin[1]
    ]
