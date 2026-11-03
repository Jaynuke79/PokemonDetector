import json
import os
import threading
import time

import pytest
import torch
from PIL import Image

pytest.importorskip("PySide6.QtWidgets", reason="needs the desktop extra")

from PySide6.QtCore import QMimeData, QPoint, Qt, QUrl
from PySide6.QtGui import QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from desktop import main as desktop_main
from desktop import window as desktop_window
from desktop.worker import (
    CLASS_NAMES_FILENAME,
    IMAGE_EXTENSIONS,
    WEIGHTS_FILENAME,
    WEIGHTS_URL,
)
from lib import detector_core

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
WAIT_SECONDS = 30


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def wait_until(condition, timeout=WAIT_SECONDS):
    deadline = time.monotonic() + timeout
    while not condition():
        if time.monotonic() > deadline:
            pytest.fail("timed out waiting for the window")
        QTest.qWait(10)


@pytest.fixture
def models_dir(weights_dir, stub_model, class_names, monkeypatch):
    torch.save(stub_model.state_dict(), weights_dir / WEIGHTS_FILENAME)
    (weights_dir / CLASS_NAMES_FILENAME).write_text(json.dumps(class_names))
    monkeypatch.setenv("POKE_MODELS_DIR", str(weights_dir))
    return weights_dir


@pytest.fixture
def model_threads(monkeypatch, stub_model):
    """Record which threads build the model and classify, using the stub model."""
    threads = {}

    def create_model(*_args, **_kwargs):
        threads["load"] = threading.get_ident()
        return stub_model

    real_predict_image = detector_core.predict_image

    def predict_image(*args, **kwargs):
        threads["classify"] = threading.get_ident()
        return real_predict_image(*args, **kwargs)

    monkeypatch.setattr("lib.detector_core.timm.create_model", create_model)
    monkeypatch.setattr("lib.detector_core.predict_image", predict_image)
    return threads


@pytest.fixture
def make_window(qapp):
    windows = []

    def make(**kwargs):
        window = desktop_window.MainWindow(**kwargs)
        windows.append(window)
        return window

    yield make
    for window in windows:
        window.close()
        window.shutdown()
        window.deleteLater()
    QTest.qWait(0)


@pytest.fixture
def loaded_window(make_window, models_dir, model_threads):
    window = make_window()
    loaded = []
    window.model_loaded.connect(lambda: loaded.append(True))
    window.start()
    wait_until(lambda: loaded)
    return window


@pytest.fixture
def image_path(tmp_path):
    path = tmp_path / "pikachu.png"
    Image.new("RGB", (32, 24), "yellow").save(path)
    return path


@pytest.fixture
def broken_image_path(tmp_path):
    path = tmp_path / "broken.png"
    path.write_bytes(b"not an image")
    return path


def open_dialogs(window):
    return [dialog for dialog in window.findChildren(QMessageBox) if dialog.isVisible()]


def wait_for_dialog(window):
    wait_until(lambda: open_dialogs(window))
    [dialog] = open_dialogs(window)
    return dialog


def classify(window, path):
    shown = []
    window.results_shown.connect(lambda: shown.append(True))
    window.open_image(str(path))
    wait_until(lambda: shown)


@pytest.mark.parametrize("extension", IMAGE_EXTENSIONS)
def test_accepts_the_web_app_formats(webapp_module, extension):
    assert webapp_module.allowed_file(f"image.{extension}")
    assert desktop_window.has_image_extension(f"image.{extension.upper()}")


@pytest.mark.parametrize("filename", ["image.webp", "image.tiff", "notes.txt", "png"])
def test_rejects_other_formats_with_a_dialog(
    webapp_module, make_window, models_dir, filename
):
    window = make_window()
    requested = []
    window.classify_requested.connect(requested.append)

    window.open_image(filename)

    dialog = wait_for_dialog(window)
    assert dialog.windowTitle() == "Unsupported file"
    assert "PNG, JPEG, GIF or BMP" in dialog.text()
    assert "Unsupported file" in window.status_label.text()
    assert requested == []
    assert not webapp_module.allowed_file(filename)


def test_results_from_the_worker_thread_reach_the_window(
    loaded_window, model_threads, image_path, class_names
):
    classify(loaded_window, image_path)

    lines = loaded_window.results.lines()
    assert len(lines) == len(class_names)
    assert [line.split(". ", 1)[0] for line in lines] == ["1", "2", "3"]
    assert {line.split(". ", 1)[1].split(":")[0] for line in lines} == set(class_names)
    assert all(line.endswith("%") for line in lines)
    assert "pikachu.png: most likely" in loaded_window.status_label.text()
    assert loaded_window.drop_area.pixmap() is not None
    assert not loaded_window.drop_area.pixmap().isNull()
    assert threading.get_ident() not in model_threads.values()
    assert set(model_threads) == {"load", "classify"}


def test_results_are_text_for_screen_readers(loaded_window, image_path):
    classify(loaded_window, image_path)

    for label, bar in zip(loaded_window.results.labels, loaded_window.results.bars):
        if label.isHidden():
            continue
        name = label.text().split(". ", 1)[1].split(":")[0]
        assert label.accessibleName() == label.text()
        assert label.focusPolicy() & Qt.TabFocus
        assert bar.accessibleName() == f"{name} confidence"
        assert bar.text() == label.text().rsplit(": ", 1)[1]


def test_window_stays_responsive_while_the_model_loads(
    make_window, models_dir, monkeypatch, stub_model
):
    release = threading.Event()

    def slow_create_model(*_args, **_kwargs):
        release.wait(WAIT_SECONDS)
        return stub_model

    monkeypatch.setattr("lib.detector_core.timm.create_model", slow_create_model)
    window = make_window()
    loaded = []
    window.model_loaded.connect(lambda: loaded.append(True))
    window.start()
    QTest.qWait(200)

    assert not loaded
    assert "Loading the model" in window.status_label.text()
    assert window.busy_bar.isVisibleTo(window)
    assert window.open_button.isEnabled()
    release.set()
    wait_until(lambda: loaded)
    assert not window.busy_bar.isVisibleTo(window)
    assert "Model loaded" in window.status_label.text()


def test_image_opened_while_loading_is_classified_after_loading(
    make_window, models_dir, model_threads, image_path
):
    window = make_window()
    window.start()

    classify(window, image_path)

    assert window.results.lines()


def test_missing_model_shows_a_dialog_with_the_download_link(
    make_window, weights_dir, class_names, monkeypatch, image_path
):
    (weights_dir / CLASS_NAMES_FILENAME).write_text(json.dumps(class_names))
    monkeypatch.setenv("POKE_MODELS_DIR", str(weights_dir))
    window = make_window()
    window.start()

    dialog = wait_for_dialog(window)

    assert dialog.windowTitle() == "Model files are missing"
    assert str(weights_dir / WEIGHTS_FILENAME) in dialog.text()
    assert WEIGHTS_URL in dialog.text()
    dialog.done(QMessageBox.Ok)
    window.open_image(str(image_path))
    assert wait_for_dialog(window).windowTitle() == "Model files are missing"


def test_corrupt_weights_show_a_dialog(
    make_window, models_dir, stub_architecture, class_names
):
    (models_dir / WEIGHTS_FILENAME).write_bytes(b"not a checkpoint")
    window = make_window()
    window.start()

    dialog = wait_for_dialog(window)

    assert dialog.windowTitle() == "Could not load the model"
    assert "Downloading it again" in dialog.text()


def test_unreadable_image_shows_a_dialog(loaded_window, broken_image_path):
    loaded_window.open_image(str(broken_image_path))

    dialog = wait_for_dialog(loaded_window)

    assert dialog.windowTitle() == "Could not read the image"
    assert "broken.png" in dialog.text()
    assert loaded_window.results.lines() == []


def test_image_in_an_unlisted_format_is_unreadable(loaded_window, tmp_path):
    path = tmp_path / "actually-a-tiff.png"
    Image.new("RGB", (8, 8)).save(path, format="TIFF")

    loaded_window.open_image(str(path))

    assert wait_for_dialog(loaded_window).windowTitle() == "Could not read the image"


def test_ctrl_o_and_enter_open_the_file_picker(loaded_window, monkeypatch, image_path):
    picks = []

    def pick(*_args, **_kwargs):
        picks.append(True)
        return str(image_path), ""

    monkeypatch.setattr(desktop_window.QFileDialog, "getOpenFileName", pick)
    loaded_window.show()
    QTest.qWaitForWindowExposed(loaded_window)

    QTest.keyClick(loaded_window, Qt.Key_O, Qt.ControlModifier)
    QTest.keyClick(loaded_window.open_button, Qt.Key_Return)
    QTest.keyClick(loaded_window.drop_area, Qt.Key_Enter)

    assert len(picks) == 3
    wait_until(lambda: loaded_window.results.lines())


def test_dropping_a_file_classifies_it(loaded_window, image_path):
    shown = []
    loaded_window.results_shown.connect(lambda: shown.append(True))
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(image_path))])
    drop = QDropEvent(QPoint(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)

    loaded_window.drop_area.dropEvent(drop)

    wait_until(lambda: shown)


def test_tab_order_and_accessible_names(loaded_window, image_path):
    classify(loaded_window, image_path)
    loaded_window.show()
    QTest.qWaitForWindowExposed(loaded_window)
    loaded_window.drop_area.setFocus()

    visited = [QApplication.focusWidget()]
    for _ in range(len(loaded_window.results.lines()) + 2):
        QTest.keyClick(QApplication.focusWidget(), Qt.Key_Tab)
        visited.append(QApplication.focusWidget())

    assert visited == [
        loaded_window.drop_area,
        loaded_window.open_button,
        *loaded_window.results.labels[: len(loaded_window.results.lines())],
        loaded_window.status_label,
    ]
    for widget in loaded_window.findChildren(QWidget):
        if widget.isVisibleTo(loaded_window) and widget.focusPolicy() & Qt.TabFocus:
            assert widget.accessibleName(), widget


def test_self_test_prints_predictions_and_exits_0(
    qapp, models_dir, model_threads, image_path, capsys
):
    assert desktop_main.main(["--self-test", str(image_path)]) == 0

    out = capsys.readouterr().out
    assert "Model loaded" in out
    assert "1. " in out


def test_self_test_saves_a_screenshot(
    qapp, models_dir, model_threads, image_path, tmp_path
):
    screenshot = tmp_path / "window.png"

    exit_code = desktop_main.main(
        ["--self-test", str(image_path), "--screenshot", str(screenshot)]
    )

    assert exit_code == 0
    with Image.open(screenshot) as image:
        assert image.width > 0 and image.height > 0


def test_self_test_exits_1_without_the_model(
    qapp, weights_dir, monkeypatch, image_path, capsys
):
    monkeypatch.setenv("POKE_MODELS_DIR", str(weights_dir))

    assert desktop_main.main(["--self-test", str(image_path)]) == 1

    assert "Model files are missing" in capsys.readouterr().err


def test_self_test_exits_1_for_an_unreadable_image(
    qapp, models_dir, model_threads, broken_image_path, capsys
):
    assert desktop_main.main(["--self-test", str(broken_image_path)]) == 1

    assert "Could not read the image" in capsys.readouterr().err


def test_self_test_exits_1_for_an_unsupported_file(
    qapp, models_dir, model_threads, tmp_path, capsys
):
    assert desktop_main.main(["--self-test", str(tmp_path / "image.webp")]) == 1

    assert "Unsupported file" in capsys.readouterr().err


def test_screenshot_needs_self_test(capsys):
    with pytest.raises(SystemExit) as exit_info:
        desktop_main.parse_args(["--screenshot", "window.png"])

    assert exit_info.value.code == 2
    assert "--screenshot needs --self-test" in capsys.readouterr().err
