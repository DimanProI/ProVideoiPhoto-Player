from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QObject

class ScreenManager(QObject):
    def __init__(self):
        super().__init__()
        self._app = QGuiApplication.instance()
        self._screens = self._app.screens()
        self._presentation_screen_index = -1
        self._app.screenAdded.connect(self._update)
        self._app.screenRemoved.connect(self._update)

    def _update(self, _=None):
        self._screens = self._app.screens()

    def get_available_screens(self):
        return self._screens

    def set_presentation_screen(self, index):
        if 0 <= index < len(self._screens):
            self._presentation_screen_index = index

    def get_presentation_screen_geometry(self):
        if 0 <= self._presentation_screen_index < len(self._screens):
            return self._screens[self._presentation_screen_index].geometry()
        return None
