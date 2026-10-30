import sys
from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image

import lib.detector_core
from cli.main import cli
from lib.detector_core import default_models_dir

PROJECT_MODELS_DIR = Path(lib.detector_core.__file__).resolve().parents[1] / "models"


@pytest.fixture(autouse=True)
def no_configured_models_dir(monkeypatch):
    monkeypatch.delenv("POKE_MODELS_DIR", raising=False)


@pytest.fixture
def frozen_bundle(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    return bundle


def test_defaults_to_project_models_dir():
    assert default_models_dir() == PROJECT_MODELS_DIR


def test_does_not_depend_on_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    assert default_models_dir() == PROJECT_MODELS_DIR


def test_frozen_build_uses_bundled_models(frozen_bundle):
    assert default_models_dir() == frozen_bundle / "models"


def test_env_var_overrides_frozen_bundle(monkeypatch, frozen_bundle, tmp_path):
    monkeypatch.setenv("POKE_MODELS_DIR", str(tmp_path / "custom"))

    assert default_models_dir() == tmp_path / "custom"


def test_empty_env_var_is_ignored(monkeypatch):
    monkeypatch.setenv("POKE_MODELS_DIR", "")

    assert default_models_dir() == PROJECT_MODELS_DIR


@pytest.fixture
def image_path(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (8, 8)).save(path)
    return path


@pytest.fixture
def models_dir(weights_dir, stub_weights, class_names_path):
    stub_weights.rename(weights_dir / "best_model_fold1.pth")
    class_names_path.rename(weights_dir / "class_names.json")
    return weights_dir


@pytest.fixture
def cwd_with_decoy_models(monkeypatch, tmp_path):
    cwd = tmp_path / "elsewhere"
    (cwd / "models").mkdir(parents=True)
    (cwd / "models" / "class_names.json").write_text("not json")
    (cwd / "models" / "best_model_fold1.pth").write_bytes(b"not a checkpoint")
    monkeypatch.chdir(cwd)


@pytest.mark.usefixtures("stub_architecture", "cwd_with_decoy_models")
def test_frozen_cli_runs_without_flags_from_any_directory(
    frozen_bundle, models_dir, image_path
):
    frozen_bundle.mkdir()
    (frozen_bundle / "models").symlink_to(models_dir)

    result = CliRunner().invoke(cli, [str(image_path), "--topk", "3"])

    assert result.exit_code == 0, result.stderr
    assert result.stdout.count("Class Index:") == 3


@pytest.mark.usefixtures("cwd_with_decoy_models")
def test_frozen_cli_reports_missing_bundled_file_as_usage_error(
    frozen_bundle, image_path
):
    result = CliRunner().invoke(cli, [str(image_path)])

    assert result.exit_code == 2
    assert isinstance(result.exception, SystemExit)
    assert "does not exist" in result.stderr


@pytest.mark.usefixtures("stub_architecture", "cwd_with_decoy_models")
def test_cli_defaults_follow_env_var(monkeypatch, models_dir, image_path):
    monkeypatch.setenv("POKE_MODELS_DIR", str(models_dir))

    result = CliRunner().invoke(cli, [str(image_path), "--topk", "3"])

    assert result.exit_code == 0, result.stderr
    assert result.stdout.count("Class Index:") == 3


@pytest.mark.usefixtures("stub_architecture")
def test_explicit_paths_override_defaults(
    monkeypatch, models_dir, image_path, tmp_path
):
    monkeypatch.setenv("POKE_MODELS_DIR", str(tmp_path / "does-not-exist"))

    result = CliRunner().invoke(
        cli,
        [
            str(image_path),
            "--topk",
            "3",
            "--weights",
            str(models_dir / "best_model_fold1.pth"),
            "--class-names-path",
            str(models_dir / "class_names.json"),
        ],
    )

    assert result.exit_code == 0, result.stderr
