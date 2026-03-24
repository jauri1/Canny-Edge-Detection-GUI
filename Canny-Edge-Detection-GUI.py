import sys
import os
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QSpinBox, QGroupBox, QGridLayout, QWidget,
    QPushButton,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QObject
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QImage, QPalette, QColor
from PIL import Image as PilImage, ImageQt
import io

PREFIX = "edges_"


class CannyWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: #303030; border: 2px dashed #666;")
        self.label = QLabel("Drop an image here", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #aaa; font-size: 14px;")

        self.label.setSizePolicy(
            self.label.sizePolicy().Policy.Ignored,
            self.label.sizePolicy().Policy.Ignored,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.label, stretch=1)

        self.image_path = None

        self.min_thresh = 25
        self.max_thresh = 75
        self.blur_ksize = 3
        self.brightness = 0
        self.contrast   = 0

        # Clipboard timer
        self._clipboard_timer = QTimer()
        self._clipboard_timer.setSingleShot(True)
        self._clipboard_timer.timeout.connect(self._copy_to_clipboard_once)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".bmp", ".tiff"):
            return
        self.image_path = path
        self.label.setText("Loading...")
        self.update_preview()

    def set_min_thresh(self, v):
        self.min_thresh = v
        self.update_preview()
        self.schedule_clipboard_copy()

    def set_max_thresh(self, v):
        self.max_thresh = v
        self.update_preview()
        self.schedule_clipboard_copy()

    def set_blur_ksize(self, v):
        self.blur_ksize = v * 2 + 1
        self.update_preview()
        self.schedule_clipboard_copy()

    def set_brightness(self, v):
        self.brightness = v
        self.update_preview()
        self.schedule_clipboard_copy()

    def set_contrast(self, v):
        self.contrast = v
        self.update_preview()
        self.schedule_clipboard_copy()

    def schedule_clipboard_copy(self):
        self._clipboard_timer.start(1000)  # 1 sec after last change

    def _copy_to_clipboard_once(self):
        if not self.image_path:
            return

        try:
            img = cv2.imread(self.image_path)
            if img is None:
                return

            scale = 1.0 + self.contrast / 100.0
            offset = self.brightness
            img = cv2.convertScaleAbs(img, alpha=scale, beta=offset)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if self.blur_ksize > 1:
                gray = cv2.GaussianBlur(gray, (self.blur_ksize, self.blur_ksize), 0)

            edges = cv2.Canny(gray, self.min_thresh, self.max_thresh)
            edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

            h, w, ch = edges_rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(
                edges_rgb.data,
                w, h,
                bytes_per_line,
                QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(qimg)
            QApplication.clipboard().setPixmap(pixmap)
            self.parent().show_notification("Copied to clipboard.")
        except Exception:
            pass

    def update_preview(self):
        if not self.image_path:
            self.label.setText("Drop an image here")
            return

        try:
            img = cv2.imread(self.image_path)
            if img is None:
                raise ValueError("Load failed")

            scale = 1.0 + self.contrast / 100.0
            offset = self.brightness
            img = cv2.convertScaleAbs(img, alpha=scale, beta=offset)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if self.blur_ksize > 1:
                gray = cv2.GaussianBlur(gray, (self.blur_ksize, self.blur_ksize), 0)

            edges = cv2.Canny(gray, self.min_thresh, self.max_thresh)
            result_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

            h, w, ch = result_rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(
                result_rgb.data,
                w, h,
                bytes_per_line,
                QImage.Format_RGB888
            )

            w0 = max(self.label.width(), 10)
            h0 = max(self.label.height(), 10)

            pixmap = QPixmap.fromImage(qimg).scaled(
                w0, h0,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.label.setPixmap(pixmap)

        except Exception as e:
            self.label.setText(f"Error: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Canny Edge Detector v1.0")
        self.resize(800, 600)

        # Dark theme
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 45))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(40, 40, 40))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(90, 120, 200))
        app.setPalette(palette)

        # Central widget
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.canny_area = CannyWidget()
        layout.addWidget(self.canny_area, stretch=3)

        # Settings
        settings = QGroupBox("Settings")
        settings.setStyleSheet("QGroupBox { font-weight: bold; }")
        sl = QGridLayout()

        rows = {
            "Min threshold": (0, 25, 0, 100),
            "Max threshold": (1, 75, 0, 100),
            "Gaussian blur": (2, 1, 0, 4),
            "Brightness": (3, 0, -100, 100),
            "Contrast": (4, 0, -100, 100),
        }

        for name, (row, defval, vmin, vmax) in rows.items():
            lab = QLabel(name)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(vmin, vmax)
            slider.setValue(defval)
            spin = QSpinBox()
            spin.setRange(vmin, vmax)
            spin.setValue(defval)

            sl.addWidget(lab, row, 0)
            sl.addWidget(slider, row, 1)
            sl.addWidget(spin, row, 2)

            if name == "Min threshold":
                slider.valueChanged.connect(self.canny_area.set_min_thresh)
                spin.valueChanged.connect(self.canny_area.set_min_thresh)
            elif name == "Max threshold":
                slider.valueChanged.connect(self.canny_area.set_max_thresh)
                spin.valueChanged.connect(self.canny_area.set_max_thresh)
            elif name == "Gaussian blur":
                slider.valueChanged.connect(self.canny_area.set_blur_ksize)
                spin.valueChanged.connect(self.canny_area.set_blur_ksize)
            elif name == "Brightness":
                slider.valueChanged.connect(self.canny_area.set_brightness)
                spin.valueChanged.connect(self.canny_area.set_brightness)
            elif name == "Contrast":
                slider.valueChanged.connect(self.canny_area.set_contrast)
                spin.valueChanged.connect(self.canny_area.set_contrast)

        settings.setLayout(sl)
        layout.addWidget(settings)

        # Notification bar (hidden by default)
        self.notification = QLabel("", self)
        self.notification.setAlignment(Qt.AlignCenter)
        self.notification.setStyleSheet(
            "background-color: #1e3a8a; color: white; padding: 6px; border-radius: 4px;"
        )
        self.notification.setFixedHeight(30)
        self.notification.hide()
        self.notification.setMaximumWidth(900)

        # Layout for notification and Export button
        extra = QHBoxLayout()
        extra.addStretch()
        extra.addWidget(self.notification, stretch=0)
        extra.addStretch()

        layout.addLayout(extra)

        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export Canny")
        self.export_btn.clicked.connect(self.export_canny)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)

        self.setCentralWidget(widget)

    def show_notification(self, text):
        self.notification.setText(text)
        self.notification.setWindowOpacity(1.0)
        self.notification.show()
        anim = QPropertyAnimation(self.notification, b"windowOpacity", self)
        anim.setDuration(5000)  # 5 seconds
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def export_canny(self):
        if not self.canny_area.image_path:
            return

        dir_, name = os.path.split(self.canny_area.image_path)
        out_path = os.path.join(dir_, PREFIX + name)

        try:
            img = cv2.imread(self.canny_area.image_path)
            if img is None:
                return

            scale = 1.0 + self.canny_area.contrast / 100.0
            offset = self.canny_area.brightness
            img = cv2.convertScaleAbs(img, alpha=scale, beta=offset)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if self.canny_area.blur_ksize > 1:
                gray = cv2.GaussianBlur(gray, (self.canny_area.blur_ksize, self.canny_area.blur_ksize), 0)

            edges = cv2.Canny(gray, self.canny_area.min_thresh, self.canny_area.max_thresh)
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            cv2.imwrite(out_path, edges)

            # Show notification only (no QMessageBox)
            self.show_notification(f"Exported: {os.path.basename(out_path)}")
        except Exception:
            self.show_notification("Export failed.")

    def save_edges(self):
        # kept for compatibility, but you now use export_canny / clipboard auto‑copy
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
