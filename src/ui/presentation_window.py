from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

class PresentationWindow(QWidget):
    """Full-screen window for secondary display."""
    window_closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProVideoiPhoto - Presentation")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        
        # Black Background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.setPalette(palette)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Video Container
        self.video_container = QWidget(self)
        self.layout.addWidget(self.video_container)
        
        # Overlay Label
        self.content_label = QLabel(self.video_container)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setStyleSheet("color: white; font-size: 24px;")
        self.content_label.hide()
        
        self.video_container.resizeEvent = lambda e: self.content_label.resize(self.video_container.size())

    def get_video_container_id(self):
        return int(self.video_container.winId())

    def set_black_screen(self, enabled):
        self.video_container.setVisible(not enabled)

    def show_image(self, pixmap):
        self.content_label.setPixmap(pixmap.scaled(self.video_container.size(), Qt.AspectRatioMode.KeepAspectRatio))
        self.content_label.show()

    def show_message(self, text):
        self.content_label.setText(text)
        self.content_label.show()
        
    def clear_content(self):
        self.content_label.clear()
        self.content_label.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape: self.close()
            
    def closeEvent(self, event):
        self.window_closed.emit()
        super().closeEvent(event)
