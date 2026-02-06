import sys
import logging
from PyQt6.QtWidgets import QApplication
from src.core.media_controller import MediaController
from src.core.playlist_manager import PlaylistManager
from src.core.screen_manager import ScreenManager
from src.ui.main_window import MainWindow

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ProVideoiPhoto")
    
    # Initialize Core Services
    media_controller = MediaController()
    playlist_manager = PlaylistManager()
    screen_manager = ScreenManager()
    
    # Initialize UI
    main_window = MainWindow(media_controller, playlist_manager, screen_manager)
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
