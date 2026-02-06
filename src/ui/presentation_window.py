from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
import logging

logger = logging.getLogger(__name__)

class PresentationWindow(QWidget):
    window_closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProVideoiPhoto - Presentation")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        
        # Set black background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder for video (the window itself will be the render target usually, 
        # but having a container is good structure)
        self.video_container = QWidget(self)
        self.layout.addWidget(self.video_container)
        
        # Image/Text overlay (for photos or when video is not active/Mock)
        self.content_label = QLabel(self.video_container)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setStyleSheet("color: white; font-size: 24px;")
        self.content_label.hide()
        
        # Resize label to fit container
        self.video_container.resizeEvent = self._on_resize

    def _on_resize(self, event):
        self.content_label.resize(self.video_container.size())

    def get_video_container_id(self):
        return int(self.video_container.winId())

    def set_black_screen(self, enabled):
        """Hides video container to show black background"""
        if enabled:
            self.video_container.hide()
        else:
            self.video_container.show()

    def show_image(self, pixmap):
        self.content_label.setPixmap(pixmap.scaled(self.video_container.size(), 
                                                 Qt.AspectRatioMode.KeepAspectRatio, 
                                                 Qt.TransformationMode.SmoothTransformation))
        self.content_label.show()

    def show_message(self, text):
        self.content_label.setText(text)
        self.content_label.show()
        
    def clear_content(self):
        self.content_label.clear()
        self.content_label.hide()

    def keyPressEvent(self, event):
        # Allow exiting fullscreen with Escape
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            
    def closeEvent(self, event):
        self.window_closed.emit()
        super().closeEvent(event)
