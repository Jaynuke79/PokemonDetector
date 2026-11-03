"""
Main window of the desktop app.

The window only handles input and display. Every model call goes to a
DetectorWorker on a separate thread, and results come back as signals.
"""

from itertools import pairwise
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QThread, Signal, Slot
from PySide6.QtGui import (
    QAccessible,
    QAccessibleAnnouncementEvent,
    QAction,
    QImage,
    QKeySequence,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop.worker import (
    IMAGE_EXTENSIONS,
    TOP_K,
    DetectorWorker,
    has_image_extension,
    unsupported_file_error,
)

APP_NAME = "Pokemon Detector"
FILE_DIALOG_FILTER = (
    "Images (" + " ".join(f"*.{extension}" for extension in IMAGE_EXTENSIONS) + ")"
)
DROP_PROMPT = "Drop an image here,\nor press Enter to choose one"
CONFIDENCE_STEPS = 10000


def _open_shortcut_text():
    return QKeySequence(QKeySequence.Open).toString(QKeySequence.NativeText)


def _readable_label():
    """A label that Tab reaches, so screen reader users can read it again later."""
    label = QLabel()
    label.setTextInteractionFlags(
        Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse
    )
    label.setFocusPolicy(Qt.StrongFocus)
    return label


class DropArea(QLabel):
    """Shows the preview, accepts dropped files and opens the picker on Enter or click."""

    file_dropped = Signal(str)
    activated = Signal()

    def __init__(self):
        super().__init__(DROP_PROMPT)
        self._preview = None
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setMinimumSize(QSize(240, 240))
        self.setAccessibleName("Image drop area")
        self.setAccessibleDescription(
            "Drop an image here, or press Enter to choose one. Shows the image preview."
        )

    def show_preview(self, image, description):
        self._preview = QPixmap.fromImage(image)
        self.setAccessibleDescription(f"Preview of {description}")
        self._fit_preview()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_preview()

    def _fit_preview(self):
        if self._preview is None:
            return
        ratio = self.devicePixelRatioF()
        scaled = self._preview.scaled(
            self.contentsRect().size() * ratio,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        scaled.setDevicePixelRatio(ratio)
        self.setPixmap(scaled)

    def dragEnterEvent(self, event):
        if any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        local_files = [
            url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()
        ]
        if local_files:
            event.acceptProposedAction()
            self.file_dropped.emit(local_files[0])

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.activated.emit()
        else:
            super().keyPressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.activated.emit()
        super().mouseReleaseEvent(event)


class ResultsPanel(QGroupBox):
    """Top predictions, each as a text label next to a confidence bar."""

    def __init__(self):
        super().__init__("Top predictions")
        self.setAccessibleName("Top predictions")
        layout = QGridLayout(self)
        layout.setColumnStretch(1, 1)
        self.labels = []
        self.bars = []
        for row in range(TOP_K):
            label = _readable_label()
            bar = QProgressBar()
            bar.setRange(0, CONFIDENCE_STEPS)
            bar.setTextVisible(True)
            layout.addWidget(label, row, 0)
            layout.addWidget(bar, row, 1)
            self.labels.append(label)
            self.bars.append(bar)
        self.clear()

    def clear(self):
        for label, bar in zip(self.labels, self.bars):
            label.hide()
            bar.hide()

    def show_predictions(self, predictions):
        self.clear()
        for rank, (label, bar, (_index, name, confidence)) in enumerate(
            zip(self.labels, self.bars, predictions), start=1
        ):
            percentage = f"{confidence * 100:.2f}%"
            label.setText(f"{rank}. {name}: {percentage}")
            label.setAccessibleName(label.text())
            bar.setValue(round(confidence * CONFIDENCE_STEPS))
            bar.setFormat(percentage)
            bar.setAccessibleName(f"{name} confidence")
            label.show()
            bar.show()

    def lines(self):
        return [label.text() for label in self.labels if not label.isHidden()]


class MainWindow(QMainWindow):
    """Window that asks a DetectorWorker for results and shows them.

    With show_dialogs=False, errors are only emitted through error_reported, so
    a self-test run never waits on a dialog nobody can close.
    """

    load_requested = Signal()
    classify_requested = Signal(str)
    model_loaded = Signal()
    results_shown = Signal()
    error_reported = Signal(str, str)

    def __init__(self, models_dir=None, show_dialogs=True):
        super().__init__()
        self._show_dialogs = show_dialogs
        self._pending_requests = 0
        self.setWindowTitle(APP_NAME)
        self.resize(720, 600)

        self.open_action = QAction("&Open image…", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self.choose_image)
        self.menuBar().addMenu("&File").addAction(self.open_action)

        self.drop_area = DropArea()
        self.drop_area.file_dropped.connect(self.open_image)
        self.drop_area.activated.connect(self.choose_image)

        self.open_button = QPushButton("&Open image…")
        self.open_button.setAutoDefault(True)
        self.open_button.setAccessibleName("Open image")
        self.open_button.setToolTip(f"Choose an image ({_open_shortcut_text()})")
        self.open_button.clicked.connect(self.choose_image)

        self.results = ResultsPanel()

        self.busy_bar = QProgressBar()
        self.busy_bar.setRange(0, 0)
        self.busy_bar.setTextVisible(False)
        self.busy_bar.setAccessibleName("Working")
        self.busy_bar.setMaximumWidth(160)
        self.busy_bar.hide()
        self.status_label = _readable_label()
        self.status_label.setWordWrap(True)
        self.status_label.setAccessibleName("Status")

        status_row = QHBoxLayout()
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.busy_bar)
        button_row = QHBoxLayout()
        button_row.addWidget(self.open_button)
        button_row.addStretch(1)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.drop_area, 1)
        layout.addLayout(button_row)
        layout.addWidget(self.results)
        layout.addLayout(status_row)
        self.setCentralWidget(central)

        focus_chain = [
            self.drop_area,
            self.open_button,
            *self.results.labels,
            self.status_label,
        ]
        for first, second in pairwise(focus_chain):
            self.setTabOrder(first, second)
        self.open_button.setFocus()

        self._thread = QThread(self)
        self.worker = DetectorWorker(models_dir)
        self.worker.moveToThread(self._thread)
        self._thread.finished.connect(self.worker.deleteLater)
        self.load_requested.connect(self.worker.load)
        self.classify_requested.connect(self.worker.classify)
        self.worker.loaded.connect(self._on_loaded)
        self.worker.load_failed.connect(self._on_load_failed)
        self.worker.classified.connect(self._on_classified)
        self.worker.classify_failed.connect(self._on_classify_failed)

    def start(self):
        """Start the worker thread and ask it to load the model."""
        self._thread.start()
        self._set_status("Loading the model, this can take a minute…")
        self._begin_request()
        self.load_requested.emit()

    def shutdown(self):
        """Stop the worker thread once its current request finishes."""
        self._thread.quit()
        self._thread.wait()

    def closeEvent(self, event):
        self.hide()
        self.shutdown()
        super().closeEvent(event)

    @Slot()
    def choose_image(self):
        path, _filter = QFileDialog.getOpenFileName(
            self, "Open image", "", FILE_DIALOG_FILTER
        )
        if path:
            self.open_image(path)

    @Slot(str)
    def open_image(self, path):
        if not has_image_extension(path):
            error = unsupported_file_error(path)
            self._report_error(error.title, error.message)
            return
        self._set_status(f"Classifying {Path(path).name}…")
        self._begin_request()
        self.classify_requested.emit(path)

    def _begin_request(self):
        self._pending_requests += 1
        self.busy_bar.show()

    def _end_request(self):
        self._pending_requests -= 1
        self.busy_bar.setVisible(self._pending_requests > 0)

    def _set_status(self, text):
        self.status_label.setText(text)
        QAccessible.updateAccessibility(
            QAccessibleAnnouncementEvent(self.status_label, text)
        )

    def _report_error(self, title, message):
        self._set_status(f"{title}. {message.splitlines()[0]}")
        if self._show_dialogs:
            dialog = QMessageBox(
                QMessageBox.Warning, title, message, QMessageBox.Ok, self
            )
            dialog.setAttribute(Qt.WA_DeleteOnClose)
            dialog.open()
        self.error_reported.emit(title, message)

    @Slot(str)
    def _on_loaded(self, device):
        self._end_request()
        if self._pending_requests == 0:
            self._set_status(
                f"Model loaded ({device}). Drop an image or press "
                f"{_open_shortcut_text()} to open one."
            )
        self.model_loaded.emit()

    @Slot(str, str)
    def _on_load_failed(self, title, message):
        self._end_request()
        self._report_error(title, message)

    @Slot(str, QImage, list)
    def _on_classified(self, path, preview, predictions):
        self._end_request()
        name = Path(path).name
        self.drop_area.show_preview(preview, name)
        self.results.show_predictions(predictions)
        top_name, top_confidence = predictions[0][1], predictions[0][2]
        self._set_status(
            f"{name}: most likely {top_name} ({top_confidence * 100:.2f}%)."
        )
        self.results_shown.emit()

    @Slot(str, str)
    def _on_classify_failed(self, title, message):
        self._end_request()
        self.results.clear()
        self._report_error(title, message)
