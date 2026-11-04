"""
Main window of the desktop app.

The window only handles input and display. Every model call goes to a
DetectorWorker on a separate thread, and results come back as signals.
"""

from itertools import pairwise
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    QThread,
    QVariantAnimation,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QAccessible,
    QAccessibleAnnouncementEvent,
    QAction,
    QColor,
    QFont,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from desktop import APP_NAME, theme
from desktop.chrome import Hinge, ScannerBody, SensorVisor, SpeakerGrille, StatusLeds
from desktop.worker import (
    IMAGE_EXTENSIONS,
    TOP_K,
    DetectorWorker,
    has_image_extension,
    unsupported_file_error,
)

FILE_DIALOG_FILTER = (
    "Images (" + " ".join(f"*.{extension}" for extension in IMAGE_EXTENSIONS) + ")"
)
DROP_PROMPT = "Drop an image here,\nor press Enter to choose one"
CARD_PLACEHOLDER = "Scan an image to see what it is."
CONFIDENCE_STEPS = 10000
MAX_TYPES = 2
SCAN_SWEEP_MS = 1600
SCAN_TRAIL = 70
BRACKET = 22


def _open_shortcut_text():
    return QKeySequence(QKeySequence.Open).toString(QKeySequence.NativeText)


def _readable_label():
    """A label that Tab reaches, so screen reader users can read it again later."""
    label = QLabel()
    label.setTextInteractionFlags(
        Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse
    )
    label.setFocusPolicy(Qt.StrongFocus)
    label.setProperty("readable", True)
    return label


def _caption(text, object_name):
    label = QLabel(text)
    label.setObjectName(object_name)
    return label


def _types_phrase(types):
    return f"{' and '.join(types)} type" if types else ""


class DropArea(QLabel):
    """The scanner screen: shows the preview, accepts dropped files, opens the
    picker on Enter or click, and sweeps a scan line while an image is classified.
    """

    file_dropped = Signal(str)
    activated = Signal()

    def __init__(self, reduced_motion=False):
        super().__init__(DROP_PROMPT)
        self.setObjectName("screen")
        self._preview = None
        self._scanning = False
        self._scan_phase = 0.0
        self._drag_over = False
        self.error_title = ""
        self.reduced_motion = reduced_motion
        self.scan_animation = QVariantAnimation(self)
        self.scan_animation.setStartValue(0.0)
        self.scan_animation.setEndValue(1.0)
        self.scan_animation.setDuration(SCAN_SWEEP_MS)
        self.scan_animation.setLoopCount(-1)
        self.scan_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.scan_animation.valueChanged.connect(self._set_scan_phase)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(QSize(220, 200))
        self.setAccessibleName("Image drop area")
        self.setAccessibleDescription(
            "Drop an image here, or press Enter to choose one. Shows the image preview."
        )

    def show_preview(self, image, description):
        self._preview = QPixmap.fromImage(image)
        self.setAccessibleDescription(f"Preview of {description}")
        self._fit_preview()

    def is_scanning(self):
        return self._scanning

    def start_scan(self):
        self.clear_error()
        self._scanning = True
        if not self.reduced_motion:
            self.scan_animation.start()
        self.update()

    def stop_scan(self):
        self._scanning = False
        self.scan_animation.stop()
        self.update()

    def show_error(self, title):
        self.error_title = title
        self.update()

    def clear_error(self):
        self.show_error("")

    def _set_scan_phase(self, phase):
        self._scan_phase = phase
        self.update()

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

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        inner = QRectF(self.rect()).adjusted(8, 8, -8, -8)
        self._paint_brackets(painter, inner)
        if self._scanning:
            self._paint_scan(painter, inner)
        if self.error_title:
            self._paint_error(painter, inner)
        if self.hasFocus():
            painter.setPen(QPen(QColor(theme.FOCUS_ON_DARK), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(4, 4, -4, -4), 9, 9)

    def _paint_brackets(self, painter, inner):
        colour = QColor(theme.SCAN_GLOW)
        colour.setAlpha(255 if self._drag_over or self._scanning else 140)
        pen = QPen(colour, 3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        for corner, dx, dy in (
            (inner.topLeft(), 1, 1),
            (inner.topRight(), -1, 1),
            (inner.bottomLeft(), 1, -1),
            (inner.bottomRight(), -1, -1),
        ):
            painter.drawLine(corner, corner + QPointF(dx * BRACKET, 0))
            painter.drawLine(corner, corner + QPointF(0, dy * BRACKET))

    def _paint_scan(self, painter, inner):
        glow = QColor(theme.SCAN_GLOW)
        painter.setPen(Qt.NoPen)
        tint = QColor(glow)
        tint.setAlpha(28)
        painter.setBrush(tint)
        painter.drawRoundedRect(inner, 6, 6)

        grid = QColor(glow)
        grid.setAlpha(34)
        painter.setPen(QPen(grid, 1))
        y = inner.top()
        while y < inner.bottom():
            painter.drawLine(QPointF(inner.left(), y), QPointF(inner.right(), y))
            y += 6

        if not self.reduced_motion:
            line_y = inner.top() + self._scan_phase * inner.height()
            trail = QLinearGradient(0, line_y - SCAN_TRAIL, 0, line_y)
            faint = QColor(glow)
            faint.setAlpha(0)
            strong = QColor(glow)
            strong.setAlpha(110)
            trail.setColorAt(0, faint)
            trail.setColorAt(1, strong)
            painter.setPen(Qt.NoPen)
            painter.setBrush(trail)
            top = max(inner.top(), line_y - SCAN_TRAIL)
            painter.drawRect(QRectF(inner.left(), top, inner.width(), line_y - top))
            halo = QColor(glow)
            halo.setAlpha(90)
            painter.setPen(QPen(halo, 7))
            painter.drawLine(
                QPointF(inner.left(), line_y), QPointF(inner.right(), line_y)
            )
            painter.setPen(QPen(QColor(theme.WHITE), 2))
            painter.drawLine(
                QPointF(inner.left(), line_y), QPointF(inner.right(), line_y)
            )

        self._paint_tag(painter, inner, "SCANNING", theme.SCREEN, theme.SCAN_GLOW)

    def _paint_tag(self, painter, inner, text, background, foreground):
        font = QFont(self.font())
        font.setBold(True)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        tag = QRectF(
            inner.left() + BRACKET + 6,
            inner.top() + 6,
            metrics.horizontalAdvance(text) + 16,
            metrics.height() + 6,
        )
        painter.setPen(QPen(QColor(foreground), 1.5))
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(tag, 5, 5)
        painter.drawText(tag, Qt.AlignCenter, text)

    def _paint_error(self, painter, inner):
        font = QFont(self.font())
        font.setBold(True)
        painter.setFont(font)
        text = f"Error: {self.error_title}"
        width = inner.width() - 20
        flags = Qt.AlignCenter | Qt.TextWordWrap
        text_rect = painter.fontMetrics().boundingRect(
            QRect(0, 0, int(width - 20), 1000), flags, text
        )
        height = text_rect.height() + 14
        banner = QRectF(inner.left() + 10, inner.bottom() - height - 10, width, height)
        painter.setPen(QPen(QColor(theme.LED_ERROR), 1.5))
        painter.setBrush(QColor(theme.ERROR_BANNER))
        painter.drawRoundedRect(banner, 7, 7)
        painter.setPen(QColor(theme.ERROR_TEXT))
        painter.drawText(banner.adjusted(10, 0, -10, 0), flags, text)

    def dragEnterEvent(self, event):
        if any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()
            self._drag_over = True
            self.update()

    def dragLeaveEvent(self, event):
        self._drag_over = False
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._drag_over = False
        self.update()
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


class TypeBadge(QLabel):
    """A pill in the colour of one elemental type."""

    def __init__(self):
        super().__init__()
        self.setObjectName("typeBadge")
        self.setFocusPolicy(Qt.NoFocus)
        self.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(12, 3, 12, 3)
        self.kind = None

    def set_kind(self, kind):
        self.kind = kind
        self.setText(kind.upper())

    def paintEvent(self, _event):
        if self.kind is None:
            return
        background = theme.TYPE_COLOURS[self.kind]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pill = QRectF(self.rect())
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(pill, pill.height() / 2, pill.height() / 2)
        painter.setPen(QColor(theme.badge_text_colour(background)))
        painter.setFont(self.font())
        painter.drawText(pill, Qt.AlignCenter, self.text())


class ResultsPanel(QFrame):
    """A card for the top prediction, with its types, and bars for the rest."""

    def __init__(self):
        super().__init__()
        self.setObjectName("resultCard")
        self.setAccessibleName("Top predictions")
        self._lines = []

        self.placeholder = _caption(CARD_PLACEHOLDER, "cardPlaceholder")
        self.placeholder.setWordWrap(True)
        self.top_confidence = _caption("", "topConfidence")
        self.top_confidence.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.others_caption = _caption("OTHER MATCHES", "othersCaption")

        self.labels = []
        self.bars = []
        for _rank in range(TOP_K):
            label = _readable_label()
            label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
            bar = QProgressBar()
            bar.setRange(0, CONFIDENCE_STEPS)
            bar.setTextVisible(False)
            self.labels.append(label)
            self.bars.append(bar)
        self.labels[0].setObjectName("topName")
        self.bars[0].setObjectName("topBar")

        self.badges = [TypeBadge() for _ in range(MAX_TYPES)]
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(5, 0, 0, 0)
        badge_row.setSpacing(6)
        for badge in self.badges:
            badge_row.addWidget(badge)
        badge_row.addStretch(1)

        confidence_row = QHBoxLayout()
        confidence_row.setSpacing(12)
        confidence_row.addWidget(self.bars[0], 1)
        confidence_row.addWidget(self.top_confidence)

        others = QGridLayout()
        others.setHorizontalSpacing(10)
        others.setVerticalSpacing(6)
        others.setColumnStretch(1, 1)
        for row, (label, bar) in enumerate(zip(self.labels[1:], self.bars[1:])):
            others.addWidget(label, row, 0)
            others.addWidget(bar, row, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(8)
        layout.addWidget(_caption("TOP MATCH", "cardCaption"))
        layout.addWidget(self.placeholder)
        layout.addWidget(self.labels[0])
        layout.addLayout(badge_row)
        layout.addLayout(confidence_row)
        layout.addSpacing(10)
        layout.addWidget(self.others_caption)
        layout.addLayout(others)
        layout.addStretch(1)
        self.clear()

    def clear(self, message=CARD_PLACEHOLDER):
        self._lines = []
        for widget in (
            *self.labels,
            *self.bars,
            *self.badges,
            self.top_confidence,
            self.others_caption,
        ):
            widget.hide()
        self.placeholder.setText(message)
        self.placeholder.show()

    def show_predictions(self, predictions, types_by_name=None):
        self.clear()
        self.placeholder.hide()
        types_by_name = types_by_name or {}
        for rank, (label, bar, (_index, name, confidence)) in enumerate(
            zip(self.labels, self.bars, predictions), start=1
        ):
            percentage = f"{confidence * 100:.2f}%"
            line = f"{rank}. {name}: {percentage}"
            self._lines.append(line)
            label.setText(name if rank == 1 else line)
            label.setAccessibleName(line)
            bar.setValue(round(confidence * CONFIDENCE_STEPS))
            bar.setFormat(percentage)
            bar.setAccessibleName(f"{name} confidence")
            label.show()
            bar.show()
        _index, top_name, top_confidence = predictions[0]
        self.top_confidence.setText(f"{top_confidence * 100:.2f}%")
        self.top_confidence.show()
        top_types = types_by_name.get(top_name, [])[:MAX_TYPES]
        self.labels[0].setAccessibleDescription(_types_phrase(top_types))
        for badge, kind in zip(self.badges, top_types):
            badge.set_kind(kind)
            badge.show()
        self.others_caption.setVisible(len(predictions) > 1)

    def lines(self):
        return list(self._lines)

    def top_types(self):
        return [badge.kind for badge in self.badges if not badge.isHidden()]


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

    def __init__(self, models_dir=None, show_dialogs=True, reduced_motion=None):
        super().__init__()
        self._show_dialogs = show_dialogs
        self._pending_requests = 0
        self._pending_classifications = 0
        self._failed = False
        self.elemental_types = theme.load_elemental_types()
        if reduced_motion is None:
            reduced_motion = theme.prefers_reduced_motion()
        self.setWindowTitle(APP_NAME)
        self.setStyleSheet(theme.STYLESHEET)
        self.resize(860, 620)

        self.open_action = QAction("&Open image…", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self.choose_image)
        self.menuBar().addMenu("&File").addAction(self.open_action)

        self.drop_area = DropArea(reduced_motion)
        self.drop_area.file_dropped.connect(self.open_image)
        self.drop_area.activated.connect(self.choose_image)

        self.open_button = QPushButton("&Open image…")
        self.open_button.setObjectName("openButton")
        self.open_button.setAutoDefault(True)
        self.open_button.setAccessibleName("Open image")
        self.open_button.setToolTip(f"Choose an image ({_open_shortcut_text()})")
        self.open_button.clicked.connect(self.choose_image)

        self.results = ResultsPanel()

        self.busy_bar = QProgressBar()
        self.busy_bar.setObjectName("busyBar")
        self.busy_bar.setRange(0, 0)
        self.busy_bar.setTextVisible(False)
        self.busy_bar.setAccessibleName("Working")
        self.busy_bar.setMaximumWidth(120)
        self.busy_bar.hide()
        self.status_label = _readable_label()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setProperty("readable", False)
        self.status_label.setWordWrap(True)
        self.status_label.setAccessibleName("Status")

        self.visor = SensorVisor()
        self.leds = StatusLeds()

        body = ScannerBody()
        header = QWidget()
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(4, 0, 4, 0)
        header_row.setSpacing(14)
        header_row.addWidget(self.visor)
        header_row.addStretch(1)
        wordmark = QVBoxLayout()
        wordmark.setSpacing(0)
        wordmark.addWidget(_caption(APP_NAME.upper(), "wordmark"), 0, Qt.AlignRight)
        wordmark.addWidget(_caption("CREATURE SCANNER", "tagline"), 0, Qt.AlignRight)
        header_row.addLayout(wordmark)
        body.seam_below = header

        bezel = QFrame()
        bezel.setObjectName("bezel")
        bezel_layout = QVBoxLayout(bezel)
        bezel_layout.setContentsMargins(16, 16, 16, 12)
        bezel_layout.setSpacing(10)
        bezel_layout.addWidget(self.drop_area, 1)
        button_row = QHBoxLayout()
        button_row.addWidget(SpeakerGrille())
        button_row.addStretch(1)
        button_row.addWidget(self.open_button)
        bezel_layout.addLayout(button_row)

        halves = QHBoxLayout()
        halves.setSpacing(10)
        halves.addWidget(bezel, 5)
        halves.addWidget(Hinge())
        halves.addWidget(self.results, 4)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.busy_bar)
        status_row.addWidget(self.leds)

        layout = QVBoxLayout(body)
        layout.setContentsMargins(26, 20, 26, 22)
        layout.setSpacing(22)
        layout.addWidget(header)
        layout.addLayout(halves, 1)
        layout.addLayout(status_row)
        self.setCentralWidget(body)

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
        self._pending_classifications += 1
        self.drop_area.start_scan()
        self.classify_requested.emit(path)

    def _begin_request(self):
        self._pending_requests += 1
        self._failed = False
        self._show_activity()

    def _end_request(self):
        self._pending_requests -= 1
        self._show_activity()

    def _end_classification(self):
        self._pending_classifications -= 1
        if self._pending_classifications == 0:
            self.drop_area.stop_scan()
        self._end_request()

    def _show_activity(self):
        busy = self._pending_requests > 0
        self.busy_bar.setVisible(busy)
        self.visor.set_active(busy)
        if busy:
            self.leds.set_state("busy")
        else:
            self.leds.set_state("error" if self._failed else "ready")

    def _set_status(self, text):
        self.status_label.setText(text)
        QAccessible.updateAccessibility(
            QAccessibleAnnouncementEvent(self.status_label, text)
        )

    def _report_error(self, title, message):
        self._failed = True
        self._show_activity()
        self.drop_area.show_error(title)
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
        self._failed = False
        self.drop_area.clear_error()
        self._end_classification()
        name = Path(path).name
        self.drop_area.show_preview(preview, name)
        self.results.show_predictions(predictions, self.elemental_types)
        top_name, top_confidence = predictions[0][1], predictions[0][2]
        self._set_status(
            f"{name}: most likely {top_name} ({top_confidence * 100:.2f}%)."
        )
        self.results_shown.emit()

    @Slot(str, str)
    def _on_classify_failed(self, title, message):
        self._end_classification()
        self.results.clear(f"No match: {title}.")
        self._report_error(title, message)
