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


@pytest.mark.parametrize("package", ["torch", "torchvision"])
def test_windows_build_cpu_pin_matches_dockerfile(package):
    dockerfile = (REPO_ROOT / "deployment" / "Dockerfile").read_text()
    build_script = (REPO_ROOT / "windows" / "build_windows.bat").read_text()
    pin = rf"\b{package}==\S+\+cpu\b"

    assert re.findall(pin, build_script) == re.findall(pin, dockerfile)


DESKTOP_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "desktop-prototype.yml"


@pytest.mark.parametrize("package", ["torch", "torchvision"])
def test_desktop_workflow_cpu_pin_matches_dockerfile(package):
    dockerfile = (REPO_ROOT / "deployment" / "Dockerfile").read_text()
    workflow = DESKTOP_WORKFLOW.read_text()
    pin = rf"\b{package}==\S+\+cpu\b"

    assert re.findall(pin, workflow) == re.findall(pin, dockerfile)


@pytest.mark.parametrize("package", ["pyinstaller", "pyinstaller-hooks-contrib"])
def test_desktop_workflow_build_pins_match_windows_build(package):
    build_script = (REPO_ROOT / "windows" / "build_windows.bat").read_text()
    workflow = DESKTOP_WORKFLOW.read_text()
    pin = rf"\b{package}==\S+"

    assert re.findall(pin, workflow) == re.findall(pin, build_script) != []


def test_desktop_workflow_pyside6_pin_matches_pyproject():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    workflow = DESKTOP_WORKFLOW.read_text()
    pin = r"\bpyside6-essentials==[\w.]+"

    assert re.findall(pin, workflow) == re.findall(pin, pyproject) != []
