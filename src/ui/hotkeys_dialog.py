from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QLabel, QKeySequenceEdit,
                               QDialogButtonBox, QMessageBox)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt

class HotkeysDialog(QDialog):
    def __init__(self, current_hotkeys, parent=None, readonly=False):
        super().__init__(parent)
        self.readonly = readonly
        self.setWindowTitle("Hotkeys Help" if readonly else "Configure Hotkeys")
        self.resize(500, 400)
        self.hotkeys = current_hotkeys.copy()
        self.key_editors = {}
        
        # Display name mapping
        self.display_names = {
            "play_pause": "Play / Pause",
            "stop": "Stop Playback",
            "prev_track": "Previous Track",
            "next_track": "Next Track",
            "black_screen": "Toggle Black Screen",
            "toggle_presentation": "Start/Stop Presentation",
            "add_files": "Add Files",
            "toggle_timer": "Start/Pause Timer",
            "reset_timer": "Reset Timer",
            "help": "Show Help"
        }
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        
        self._populate_table()
        
        layout.addWidget(self.table)
        
        # Footer Label (Copyright)
        copyright_label = QLabel("Продукт был создан Дмитрием Сальниковым для открытого распространения, все права защищены")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 10px;")
        copyright_label.setWordWrap(True)
        layout.addWidget(copyright_label)
        
        # Buttons
        btns = QDialogButtonBox.StandardButton.Ok
        if not self.readonly:
            btns |= QDialogButtonBox.StandardButton.Cancel
            
        button_box = QDialogButtonBox(btns)
        button_box.accepted.connect(self.accept)
        if not self.readonly:
            button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_table(self):
        self.table.setRowCount(len(self.hotkeys))
        
        for i, (action, key_seq) in enumerate(self.hotkeys.items()):
            # Action Name
            name_item = QTableWidgetItem(self.display_names.get(action, action))
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled) # Read only
            self.table.setItem(i, 0, name_item)
            
            # Key Display/Editor
            if self.readonly:
                key_item = QTableWidgetItem(key_seq)
                key_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(i, 1, key_item)
            else:
                editor = QKeySequenceEdit(QKeySequence(key_seq))
                # Store action key to retrieve later
                editor.setProperty("action_key", action)
                self.table.setCellWidget(i, 1, editor)
                self.key_editors[action] = editor

    def get_hotkeys(self):
        """Return the updated hotkeys dictionary"""
        updated_hotkeys = {}
        for action, editor in self.key_editors.items():
            seq = editor.keySequence().toString()
            updated_hotkeys[action] = seq
        return updated_hotkeys
