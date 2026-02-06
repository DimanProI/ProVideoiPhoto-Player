from PyQt6.QtGui import QScreen, QGuiApplication
from PyQt6.QtCore import QObject, pyqtSignal, QRect
import logging

logger = logging.getLogger(__name__)

class ScreenManager(QObject):
    screens_changed = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self._app = QGuiApplication.instance()
        self._screens = self._app.screens()
        self._presentation_screen_index = -1
        
        self._app.screenAdded.connect(self._update_screens)
        self._app.screenRemoved.connect(self._update_screens)

    def _update_screens(self, screen=None):
        self._screens = self._app.screens()
        screen_names = [s.name() for s in self._screens]
        logger.info(f"Screens updated: {screen_names}")
        self.screens_changed.emit(self._screens)

    def get_available_screens(self):
        return self._screens

    def set_presentation_screen(self, index):
        if 0 <= index < len(self._screens):
            self._presentation_screen_index = index
            logger.info(f"Presentation screen set to index {index}: {self._screens[index].name()}")
            return True
        return False

    def get_presentation_screen_geometry(self):
        if 0 <= self._presentation_screen_index < len(self._screens):
            return self._screens[self._presentation_screen_index].geometry()
        return None
    
    def get_screen_count(self):
        return len(self._screens)
