from __future__ import annotations
import threading
from typing import Optional, Callable

import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets


class FrameBridge(QtCore.QObject):
    frameReady = QtCore.pyqtSignal(QtGui.QImage)

    @QtCore.pyqtSlot(np.ndarray)
    def update_frame(self, frame_bgr: np.ndarray):
        h, w, ch = frame_bgr.shape
        bytes_per_line = ch * w
        # Convert BGR numpy array to RGB QImage for broad compatibility
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        qimg = QtGui.QImage(frame_rgb.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        # Deep copy to ensure data remains valid after function returns
        qimg = qimg.copy()
        self.frameReady.emit(qimg)


class DisplayWindow(QtWidgets.QMainWindow):
    def __init__(self, title: str = "Display", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.label = QtWidgets.QLabel()
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.label)
        self.setMinimumSize(640, 360)

    @QtCore.pyqtSlot(QtGui.QImage)
    def on_frame(self, img: QtGui.QImage):
        pix = QtGui.QPixmap.fromImage(img)
        self.label.setPixmap(pix.scaled(self.label.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        # Rescale current pixmap on resize for better fit
        pix = self.label.pixmap()
        if pix:
            self.label.setPixmap(pix.scaled(self.label.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        super().resizeEvent(event)


class ControlWindow(QtWidgets.QMainWindow):
    startRecording = QtCore.pyqtSignal(int)  # duration seconds
    filterChanged = QtCore.pyqtSignal(str)
    moveDisplayToScreen = QtCore.pyqtSignal(int)

    def __init__(self, display: DisplayWindow, parent=None):
        super().__init__(parent)
        self.display = display
        self.setWindowTitle("Control Panel")
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)

        # Recording controls
        self.durationSpin = QtWidgets.QSpinBox()
        self.durationSpin.setRange(3, 60)
        self.durationSpin.setValue(10)
        self.btnRecord = QtWidgets.QPushButton("Record (Countdown)")
        self.btnRecord.clicked.connect(self._on_record)

        # Filter selection
        self.filterCombo = QtWidgets.QComboBox()
        self.filterCombo.addItems(["glow", "density", "trails"])
        self.filterCombo.currentTextChanged.connect(self._on_filter)

        # Screen selection
        self.screenCombo = QtWidgets.QComboBox()
        for idx, scr in enumerate(QtWidgets.QApplication.screens()):
            self.screenCombo.addItem(f"Screen {idx}: {scr.name()}")
        self.btnMove = QtWidgets.QPushButton("Move Display to Screen")
        self.btnMove.clicked.connect(self._on_move)

        layout.addWidget(QtWidgets.QLabel("Duration (s):"))
        layout.addWidget(self.durationSpin)
        layout.addWidget(self.btnRecord)
        layout.addSpacing(12)
        layout.addWidget(QtWidgets.QLabel("Filter:"))
        layout.addWidget(self.filterCombo)
        layout.addSpacing(12)
        layout.addWidget(QtWidgets.QLabel("Display Screen:"))
        layout.addWidget(self.screenCombo)
        layout.addWidget(self.btnMove)

        central.setLayout(layout)
        self.setCentralWidget(central)
        self.setMinimumSize(360, 240)

    def _on_record(self):
        self.startRecording.emit(int(self.durationSpin.value()))

    def _on_filter(self, text: str):
        self.filterChanged.emit(text)

    def _on_move(self):
        idx = int(self.screenCombo.currentIndex())
        self.moveDisplayToScreen.emit(idx)


class AppGUI:
    def __init__(self, start_capture_cb: Callable[[int], None], set_filter_cb: Callable[[str], None]):
        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        self.display = DisplayWindow("Silhouette Display")
        self.control = ControlWindow(self.display)

        self.bridge = FrameBridge()
        self.bridge.frameReady.connect(self.display.on_frame)

        # Connect control signals
        self.control.startRecording.connect(lambda dur: threading.Thread(target=start_capture_cb, args=(dur,), daemon=True).start())
        self.control.filterChanged.connect(set_filter_cb)
        self.control.moveDisplayToScreen.connect(self._move_display_to_screen)

        self.display.show()
        self.control.show()

    def _move_display_to_screen(self, screen_index: int):
        screens = QtWidgets.QApplication.screens()
        if 0 <= screen_index < len(screens):
            scr = screens[screen_index]
            geo = scr.geometry()
            self.display.move(geo.topLeft())
            self.display.resize(geo.size())
            self.display.showFullScreen()

    # External API
    def push_frame(self, frame_bgr: np.ndarray):
        self.bridge.update_frame(frame_bgr)

    def run(self):
        return self.app.exec()
