import os
from PyQt6.QtCore import QAbstractListModel, Qt, pyqtSignal

class PlaylistItem:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

class PlaylistManager(QAbstractListModel):
    current_item_changed = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self._items = []
        self._current_index = -1

    def rowCount(self, parent=None): return len(self._items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._items)): return None
        if role == Qt.ItemDataRole.DisplayRole: return self._items[index.row()].filename
        if role == Qt.ItemDataRole.UserRole: return self._items[index.row()]
        return None

    def add_file(self, filepath):
        if not os.path.exists(filepath): return
        self.beginInsertRows(self.index(0), len(self._items), len(self._items))
        self._items.append(PlaylistItem(filepath))
        self.endInsertRows()
        if self._current_index == -1: self.set_current_index(0)

    def set_current_index(self, index):
        if 0 <= index < len(self._items):
            self._current_index = index
            self.current_item_changed.emit(self._items[index])

    def next(self):
        if self._current_index + 1 < len(self._items):
            self.set_current_index(self._current_index + 1)

    def previous(self):
        if self._current_index - 1 >= 0:
            self.set_current_index(self._current_index - 1)
