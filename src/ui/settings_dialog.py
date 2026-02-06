from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, 
                               QDialogButtonBox, QFormLayout, QSlider)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    def __init__(self, screen_manager, media_controller, parent=None):
        super().__init__(parent)
        self.screen_manager = screen_manager
        self.media_controller = media_controller
        self.setWindowTitle("Settings")
        self.resize(400, 250)
        
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Screen Selection
        self.screen_combo = QComboBox()
        screens = self.screen_manager.get_available_screens()
        for i, screen in enumerate(screens):
            self.screen_combo.addItem(f"Monitor {i+1}: {screen.name()} ({screen.geometry().width()}x{screen.geometry().height()})", i)
            
        form_layout.addRow("Presentation Monitor:", self.screen_combo)
        
        # Volume Control
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_label = QLabel("100%")
        self.volume_slider.valueChanged.connect(lambda v: self.volume_label.setText(f"{v}%"))
        
        volume_layout = QVBoxLayout()
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        
        form_layout.addRow("Volume:", volume_layout)
        
        layout.addLayout(form_layout)
        
        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _load_settings(self):
        # Load Screen
        current_index = self.screen_manager._presentation_screen_index
        if current_index >= 0:
            self.screen_combo.setCurrentIndex(current_index)
        elif self.screen_combo.count() > 1:
            self.screen_combo.setCurrentIndex(1)
        else:
            self.screen_combo.setCurrentIndex(0)
            
        # Load Volume
        current_vol = int(self.media_controller.get_volume())
        self.volume_slider.setValue(current_vol)
        self.volume_label.setText(f"{current_vol}%")

    def get_selected_screen_index(self):
        return self.screen_combo.currentData()
        
    def get_volume(self):
        return self.volume_slider.value()
