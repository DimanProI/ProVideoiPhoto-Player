from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                               QLabel, QDialogButtonBox, QKeySequenceEdit)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt

class HotkeysDialog(QDialog):
    def __init__(self, current_hotkeys, parent=None, readonly=False):
        super().__init__(parent)
        self.readonly = readonly
        self.setWindowTitle("Hotkeys")
        self.resize(500, 400)
        self.hotkeys = current_hotkeys.copy()
        self.key_editors = {}
        self.display_names = {
            "play_pause": "Play / Pause", "stop": "Stop", "prev_track": "Prev Track",
            "next_track": "Next Track", "black_screen": "Toggle Black Screen",
            "toggle_presentation": "Toggle Presentation", "add_files": "Add Files",
            "toggle_timer": "Toggle Timer", "reset_timer": "Reset Timer", "help": "Help"
        }
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self._populate_table()
        layout.addWidget(self.table)
        
        copy_label = QLabel("Продукт был создан Дмитрием Сальниковым для открытого распространения, все права защищены")
        copy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copy_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 10px;")
        copy_label.setWordWrap(True)
        layout.addWidget(copy_label)
        
        btns = QDialogButtonBox.StandardButton.Ok
        if not self.readonly: btns |= QDialogButtonBox.StandardButton.Cancel
        box = QDialogButtonBox(btns)
        box.accepted.connect(self.accept)
        if not self.readonly: box.rejected.connect(self.reject)
        layout.addWidget(box)

    def _populate_table(self):
        self.table.setRowCount(len(self.hotkeys))
        for i, (action, seq) in enumerate(self.hotkeys.items()):
            self.table.setItem(i, 0, QTableWidgetItem(self.display_names.get(action, action)))
            if self.readonly:
                self.table.setItem(i, 1, QTableWidgetItem(seq))
            else:
                editor = QKeySequenceEdit(QKeySequence(seq))
                self.table.setCellWidget(i, 1, editor)
                self.key_editors[action] = editor

    def get_hotkeys(self):
        return {action: ed.keySequence().toString() for action, ed in self.key_editors.items()}
