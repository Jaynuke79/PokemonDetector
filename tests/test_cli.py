import pytest
from click.testing import CliRunner
from PIL import Image

from cli.main import cli


@pytest.fixture
def image_path(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (8, 8)).save(path)
    return path


@pytest.fixture
def run_cli(image_path, class_names_path, stub_weights, stub_architecture):
    def run(*args, image=image_path, weights=stub_weights, names=class_names_path):
        return CliRunner().invoke(
            cli,
            [
                str(image),
                "--weights",
                str(weights),
                "--class-names-path",
                str(names),
                *args,
            ],
        )

    return run


def assert_usage_error(result, expected_in_stderr):
    assert result.exit_code == 2
    assert isinstance(result.exception, SystemExit)
    assert expected_in_stderr in result.stderr


def test_prints_predictions(run_cli):
    result = run_cli("--topk", "3")

    assert result.exit_code == 0
    assert result.stdout.count("Class Index:") == 3


def test_verbose_is_a_flag(run_cli):
    result = run_cli("--topk", "1", "--verbose")

    assert result.exit_code == 0
    assert "Using device:" in result.stdout


def test_verbose_rejects_a_value(run_cli):
    assert_usage_error(run_cli("--verbose", "true"), "unexpected extra argument")


def test_model_load_failure_exits_nonzero_with_cause_on_stderr(
    run_cli, corrupt_weights
):
    result = run_cli("--topk", "1", weights=corrupt_weights)

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert "Could not load model:" in result.stderr
    assert "Class Index:" not in result.stdout


@pytest.mark.parametrize("topk", ["500", "4"])
def test_topk_above_class_count_is_a_usage_error(run_cli, topk):
    assert_usage_error(run_cli("--topk", topk), "available classes")


@pytest.mark.parametrize("topk", ["0", "-1"])
def test_topk_below_one_is_a_usage_error(run_cli, topk):
    assert_usage_error(run_cli("--topk", topk), "--topk")


def test_missing_image_is_a_usage_error(run_cli, tmp_path):
    result = run_cli(image=tmp_path / "missing.png")

    assert_usage_error(result, "does not exist")


def test_missing_class_names_is_a_usage_error(run_cli, tmp_path):
    result = run_cli(names=tmp_path / "missing.json")

    assert_usage_error(result, "does not exist")


def test_missing_weights_is_a_usage_error(run_cli, tmp_path):
    result = run_cli(weights=tmp_path / "missing.pth")

    assert_usage_error(result, "does not exist")
