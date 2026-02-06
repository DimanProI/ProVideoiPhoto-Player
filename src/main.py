import sys
import logging
import os
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.core.media_controller import MediaController
from src.core.playlist_manager import PlaylistManager
from src.core.screen_manager import ScreenManager
from src.ui.main_window import MainWindow

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ProVideoiPhoto")
    
    # Taskbar Icon Fix for Windows
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('mycompany.provideoiphoto.player.1.0')
    except:
        pass
    
    # Resolve Application Path
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            app_path = sys._MEIPASS
        else:
            app_path = os.path.dirname(sys.executable)
    else:
        app_path = os.path.dirname(os.path.dirname(__file__))
        
    # Load Icon
    icon_path = os.path.join(app_path, 'assets', 'icon.png')
    if not os.path.exists(icon_path):
        icon_path = os.path.join(app_path, '..', 'assets', 'icon.png')
        
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Initialize Core & UI
    media_controller = MediaController()
    playlist_manager = PlaylistManager()
    screen_manager = ScreenManager()
    
    main_window = MainWindow(media_controller, playlist_manager, screen_manager)
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
