import os
from PyQt6.QtCore import QObject, pyqtSignal, QAbstractListModel, Qt
import logging

logger = logging.getLogger(__name__)

class PlaylistItem:
    def __init__(self, filepath, duration=0.0):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.duration = duration
        self.notes = ""

class PlaylistManager(QAbstractListModel):
    current_item_changed = pyqtSignal(object) # Emits PlaylistItem
    
    def __init__(self):
        super().__init__()
        self._items = []
        self._current_index = -1

    def rowCount(self, parent=None):
        return len(self._items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None
        
        item = self._items[index.row()]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return item.filename
        elif role == Qt.ItemDataRole.UserRole:
            return item
        
        return None

    def add_file(self, filepath):
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return
            
        self.beginInsertRows(self.index(0), len(self._items), len(self._items))
        item = PlaylistItem(filepath)
        self._items.append(item)
        self.endInsertRows()
        
        if self._current_index == -1:
            self.set_current_index(0)

    def remove_file(self, index):
        if 0 <= index < len(self._items):
            self.beginRemoveRows(self.index(0), index, index)
            self._items.pop(index)
            self.endRemoveRows()
            
            # Adjust current index if needed
            if index == self._current_index:
                # If we removed the current item, try to select the next one, or the previous one
                if index < len(self._items):
                    self.set_current_index(index)
                elif len(self._items) > 0:
                    self.set_current_index(len(self._items) - 1)
                else:
                    self._current_index = -1
                    self.current_item_changed.emit(None)
            elif index < self._current_index:
                self._current_index -= 1

    def get_current_item(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return None

    def set_current_index(self, index):
        if 0 <= index < len(self._items):
            self._current_index = index
            self.current_item_changed.emit(self._items[index])

    def next(self):
        if self._current_index + 1 < len(self._items):
            self.set_current_index(self._current_index + 1)
            return True
        return False

    def previous(self):
        if self._current_index - 1 >= 0:
            self.set_current_index(self._current_index - 1)
            return True
        return False
