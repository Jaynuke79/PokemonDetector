"""
Painted, decorative parts of the scanner body. None of them take focus.

The status they hint at is always in the status text as well. Each part draws
in unscaled units and multiplies its size and painting by the window's scale.
"""

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QSizePolicy, QWidget

from desktop import theme

BODY_MARGIN = 8
BODY_RADIUS = 26
LED_COLOURS = {
    "ready": theme.LED_READY,
    "busy": theme.LED_BUSY,
    "error": theme.LED_ERROR,
}


class ScaledPart(QWidget):
    def __init__(self, scale, decorative=True):
        super().__init__()
        self.scale = scale
        if decorative:
            self.setFocusPolicy(Qt.NoFocus)
            self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def scaled_size(self, width, height):
        return QSize(round(width * self.scale), round(height * self.scale))

    def begin_painting(self):
        """Return an antialiased painter in unscaled units, and the area to fill."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(self.scale, self.scale)
        area = QRectF(0, 0, self.width() / self.scale, self.height() / self.scale)
        return painter, area


class ScannerBody(ScaledPart):
    """The red handheld shell everything else sits on."""

    def __init__(self, scale=1.0):
        super().__init__(scale, decorative=False)
        self.setObjectName("body")
        self.seam_below = None

    def paintEvent(self, _event):
        painter, area = self.begin_painting()
        painter.fillRect(area, QColor(theme.DESK))
        body = area.adjusted(BODY_MARGIN, BODY_MARGIN, -BODY_MARGIN, -BODY_MARGIN)
        shade = QLinearGradient(body.topLeft(), body.bottomLeft())
        shade.setColorAt(0, QColor(theme.BODY_RED_LIGHT))
        shade.setColorAt(0.08, QColor(theme.BODY_RED))
        shade.setColorAt(1, QColor(theme.BODY_RED_DARK))
        painter.setPen(QPen(QColor(theme.BODY_RED_DARK), 2))
        painter.setBrush(shade)
        painter.drawRoundedRect(body, BODY_RADIUS, BODY_RADIUS)

        if self.seam_below is None:
            return
        seam_y = self.seam_below.geometry().bottom() / self.scale + 10
        painter.setPen(QPen(QColor(theme.BODY_RED_DARK), 3))
        painter.drawLine(
            QPointF(body.left() + BODY_RADIUS, seam_y),
            QPointF(body.right() - BODY_RADIUS, seam_y),
        )
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
        painter.drawLine(
            QPointF(body.left() + BODY_RADIUS, seam_y + 2),
            QPointF(body.right() - BODY_RADIUS, seam_y + 2),
        )


class SensorVisor(ScaledPart):
    """A glass capsule on the top edge that glows brighter while busy."""

    def __init__(self, scale=1.0):
        super().__init__(scale)
        self._active = False
        self.setFixedSize(self.scaled_size(92, 34))

    def set_active(self, active):
        self._active = active
        self.update()

    def paintEvent(self, _event):
        painter, area = self.begin_painting()
        outer = area.adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(theme.SHELL), 3))
        painter.setBrush(QColor(theme.SCREEN))
        painter.drawRoundedRect(outer, outer.height() / 2, outer.height() / 2)

        glass = outer.adjusted(5, 5, -5, -5)
        glow = QRadialGradient(glass.center(), glass.width() / 1.6)
        core = QColor(theme.SCAN_GLOW)
        core.setAlpha(255 if self._active else 150)
        rim = QColor(theme.BAR_FILL)
        rim.setAlpha(200 if self._active else 90)
        glow.setColorAt(0, core)
        glow.setColorAt(1, rim)
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawRoundedRect(glass, glass.height() / 2, glass.height() / 2)

        painter.setBrush(QColor(255, 255, 255, 170))
        shine = QRectF(glass.left() + 8, glass.top() + 3, glass.width() * 0.35, 4)
        painter.drawRoundedRect(shine, 2, 2)


class StatusLeds(ScaledPart):
    """Ready, busy and error indicator lights."""

    DIAMETER = 12
    GAP = 8

    def __init__(self, scale=1.0):
        super().__init__(scale)
        self.state = None
        count = len(LED_COLOURS)
        self.setFixedSize(
            self.scaled_size(
                count * self.DIAMETER + (count - 1) * self.GAP + 4, self.DIAMETER + 4
            )
        )

    def set_state(self, state):
        self.state = state
        self.update()

    def paintEvent(self, _event):
        painter, _area = self.begin_painting()
        for index, state in enumerate(LED_COLOURS):
            rect = QRectF(
                2 + index * (self.DIAMETER + self.GAP), 2, self.DIAMETER, self.DIAMETER
            )
            lit = state == self.state
            colour = QColor(LED_COLOURS[state] if lit else theme.LED_OFF)
            painter.setPen(QPen(QColor(theme.BODY_RED_DARK), 1.5))
            painter.setBrush(colour)
            painter.drawEllipse(rect)
            if lit:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(255, 255, 255, 150))
                painter.drawEllipse(QRectF(rect.left() + 3, rect.top() + 2.5, 4, 3.5))


class Hinge(ScaledPart):
    """The barrel hinge between the screen half and the result half."""

    KNUCKLES = 4

    def __init__(self, scale=1.0):
        super().__init__(scale)
        self.setFixedWidth(round(22 * scale))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def paintEvent(self, _event):
        painter, area = self.begin_painting()
        area = area.adjusted(3, 10, -3, -10)
        barrel = QLinearGradient(area.topLeft(), area.topRight())
        barrel.setColorAt(0, QColor(theme.BODY_RED_DARK))
        barrel.setColorAt(0.45, QColor(theme.BODY_RED_LIGHT))
        barrel.setColorAt(1, QColor(theme.BODY_RED_DARK))
        painter.setPen(Qt.NoPen)
        painter.setBrush(barrel)
        painter.drawRoundedRect(area, area.width() / 2, area.width() / 2)

        gap = 6
        height = (area.height() - gap * (self.KNUCKLES - 1)) / self.KNUCKLES
        painter.setPen(QPen(QColor(theme.DESK), 2))
        for index in range(1, self.KNUCKLES):
            y = area.top() + index * (height + gap) - gap / 2
            painter.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))


class SpeakerGrille(ScaledPart):
    """Slots under the screen, beside a small red power light."""

    SLOTS = 4

    def __init__(self, scale=1.0):
        super().__init__(scale)
        self.setFixedSize(self.scaled_size(74, 24))

    def paintEvent(self, _event):
        painter, area = self.begin_painting()
        painter.setPen(QPen(QColor(theme.BODY_RED_DARK), 1.5))
        painter.setBrush(QColor(theme.BODY_RED))
        painter.drawEllipse(QRectF(2, 6, 12, 12))
        slot_pen = QPen(QColor(theme.INK_MUTED), 3)
        slot_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(slot_pen)
        for index in range(self.SLOTS):
            y = 5 + index * 4.5
            painter.drawLine(QPointF(26, y), QPointF(area.width() - 4, y))
