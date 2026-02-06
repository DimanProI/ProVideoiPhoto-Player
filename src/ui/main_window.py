from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QSplitter, QFrame, QFileDialog, 
                               QListWidget, QListWidgetItem, QComboBox, QSlider, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QTime, QSettings
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
import os

from src.ui.presentation_window import PresentationWindow
from src.utils.thumbnail_generator import ThumbnailGenerator
from src.ui.hotkeys_dialog import HotkeysDialog

class ClickableSlider(QSlider):
    """Slider that jumps to click position."""
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.position().x()) / self.width()
            self.setValue(int(round(val)))
            self.sliderPressed.emit()
            self.sliderMoved.emit(int(round(val)))

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.sliderReleased.emit()

class MainWindow(QMainWindow):
    def __init__(self, media_controller, playlist_manager, screen_manager):
        super().__init__()
        self.media_controller = media_controller
        self.playlist_manager = playlist_manager
        self.screen_manager = screen_manager
        self.presentation_window = None
        
        # Configuration
        self.settings = QSettings("ProVideoiPhoto", "AppConfig")
        self.shortcuts = {} 
        self._init_hotkeys_data()
        
        # State
        self.presentation_timer = QTimer()
        self.presentation_timer.timeout.connect(self._update_timer)
        self.elapsed_time = QTime(0, 0, 0)
        self.is_timer_running = False
        self.is_seeking = False
        self.duration = 0
        
        # UI Setup
        self.setWindowTitle("ProVideoiPhoto - Control Panel")
        self.resize(1200, 800)
        self.setAcceptDrops(True)
        self._set_app_icon()
        self._init_ui()
        self._connect_signals()
        self._apply_hotkeys()
        
        # Mock Warning
        if self.media_controller.is_mock:
            QTimer.singleShot(500, self._show_mock_warning)

    def _set_app_icon(self):
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        icon_path = os.path.join(base_path, 'assets', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _show_mock_warning(self):
        QMessageBox.warning(self, "Video Engine Missing", 
                          "Could not load 'libmpv'.\n"
                          "Video playback will be simulated.\n"
                          "Please install libmpv to enable 4K playback.")

    def _init_hotkeys_data(self):
        self.default_hotkeys = {
            "play_pause": "Space", "stop": "Esc", "prev_track": "Left", "next_track": "Right",
            "black_screen": "B", "toggle_presentation": "F5", "add_files": "Ctrl+O",
            "toggle_timer": "T", "reset_timer": "R", "help": "F1"
        }
        self.current_hotkeys = self.settings.value("hotkeys", self.default_hotkeys)
        if not isinstance(self.current_hotkeys, dict): self.current_hotkeys = self.default_hotkeys

    def _apply_hotkeys(self):
        for s in self.shortcuts.values(): s.setEnabled(False)
        self.shortcuts.clear()
        
        actions_map = {
            "play_pause": self._toggle_play, "stop": self._stop_playback,
            "prev_track": self._prev_track, "next_track": self._next_track,
            "black_screen": self._toggle_black_screen, "toggle_presentation": self._toggle_presentation_screen,
            "add_files": self._add_files, "toggle_timer": self._toggle_timer,
            "reset_timer": self._reset_timer, "help": self._show_help
        }
        
        for name, seq in self.current_hotkeys.items():
            if name in actions_map and seq:
                shortcut = QShortcut(QKeySequence(seq), self)
                shortcut.activated.connect(actions_map[name])
                self.shortcuts[name] = shortcut
                self._update_tooltip(name, seq)

    def _update_tooltip(self, name, seq):
        widgets = {
            "play_pause": self.play_btn, "stop": self.stop_btn, "prev_track": self.prev_btn,
            "next_track": self.next_btn, "black_screen": self.black_btn, 
            "toggle_presentation": self.screen_selector_btn, "add_files": self.add_file_btn,
            "toggle_timer": self.timer_btn, "reset_timer": self.reset_timer_btn, "help": self.help_btn
        }
        if name in widgets: widgets[name].setToolTip(f"Shortcut: {seq}")

    def _show_help(self):
        HotkeysDialog(self.current_hotkeys, self, readonly=True).exec()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Top Bar
        top = QHBoxLayout()
        self.screen_combo = QComboBox()
        self.screen_combo.setMinimumWidth(200)
        self.screen_combo.currentIndexChanged.connect(self._on_screen_selection_changed)
        self._update_screen_combo()
        top.addWidget(self.screen_combo)
        
        self.screen_selector_btn = QPushButton("Start Presentation")
        self.screen_selector_btn.clicked.connect(self._toggle_presentation_screen)
        top.addWidget(self.screen_selector_btn)
        top.addStretch()
        
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        top.addWidget(self.timer_label)
        
        self.timer_btn = QPushButton("Start Timer")
        self.timer_btn.clicked.connect(self._toggle_timer)
        top.addWidget(self.timer_btn)
        
        self.reset_timer_btn = QPushButton("Reset")
        self.reset_timer_btn.clicked.connect(self._reset_timer)
        top.addWidget(self.reset_timer_btn)
        
        self.help_btn = QPushButton("Help (F1)")
        self.help_btn.clicked.connect(self._show_help)
        top.addWidget(self.help_btn)
        top.addStretch()
        layout.addLayout(top)
        
        # Main Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(5)
        self.main_splitter.setStyleSheet("QSplitter::handle { background-color: #444; } QSplitter::handle:hover { background-color: #666; }")
        layout.addWidget(self.main_splitter, 1)
        
        # Left: Playlist
        playlist_widget = QWidget()
        plist_layout = QVBoxLayout(playlist_widget)
        plist_layout.addWidget(QLabel("Playlist"))
        
        self.add_file_btn = QPushButton("Add Files")
        self.add_file_btn.clicked.connect(self._add_files)
        plist_layout.addWidget(self.add_file_btn)
        
        self.playlist_view = QListWidget()
        self.playlist_view.itemDoubleClicked.connect(self._on_playlist_item_dbl_click)
        plist_layout.addWidget(self.playlist_view)
        self.main_splitter.addWidget(playlist_widget)
        
        # Right: Previews & Controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.main_splitter.addWidget(right_panel)
        
        # Preview Splitter
        self.previews_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.previews_splitter.setHandleWidth(5)
        self.previews_splitter.setStyleSheet("QSplitter::handle { background-color: #444; } QSplitter::handle:hover { background-color: #666; }")
        
        # Current Preview
        self.current_preview_frame = QFrame()
        self.current_preview_frame.setMinimumSize(400, 225)
        self.current_preview_frame.setStyleSheet("background-color: black;")
        p_layout = QVBoxLayout(self.current_preview_frame)
        p_layout.setContentsMargins(0,0,0,0)
        self.preview_label = QLabel("No Media Selected")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: gray; font-size: 14px;")
        p_layout.addWidget(self.preview_label)
        self.previews_splitter.addWidget(self.current_preview_frame)
        
        # Next Preview
        self.next_preview_frame = QFrame()
        self.next_preview_frame.setMinimumSize(160, 90)
        self.next_preview_frame.setStyleSheet("background-color: #222;")
        self.previews_splitter.addWidget(self.next_preview_frame)
        
        self.previews_splitter.setStretchFactor(0, 7)
        self.previews_splitter.setStretchFactor(1, 3)
        right_layout.addWidget(self.previews_splitter, 1)
        
        # Seek Bar
        seek_layout = QHBoxLayout()
        self.time_current_label = QLabel("00:00")
        seek_layout.addWidget(self.time_current_label)
        
        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.seek_slider.sliderPressed.connect(self._on_seek_slider_pressed)
        self.seek_slider.sliderReleased.connect(self._on_seek_slider_released)
        self.seek_slider.sliderMoved.connect(self._on_seek_slider_moved)
        seek_layout.addWidget(self.seek_slider)
        
        self.time_total_label = QLabel("00:00")
        seek_layout.addWidget(self.time_total_label)
        right_layout.addLayout(seek_layout)
        
        # Media Controls
        ctrl_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Prev")
        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")
        self.next_btn = QPushButton("Next")
        self.black_btn = QPushButton("Black Screen")
        
        for b in [self.prev_btn, self.play_btn, self.stop_btn, self.next_btn]:
            ctrl_layout.addWidget(b)
            
        ctrl_layout.addSpacing(20)
        ctrl_layout.addWidget(QLabel("Vol:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(lambda v: self.media_controller.set_volume(v))
        ctrl_layout.addWidget(self.volume_slider)
        
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.black_btn)
        right_layout.addLayout(ctrl_layout)
        
        # Connections
        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop_playback)
        self.prev_btn.clicked.connect(self._prev_track)
        self.next_btn.clicked.connect(self._next_track)
        self.black_btn.clicked.connect(self._toggle_black_screen)
        
        self.main_splitter.setSizes([360, 840])

    def _connect_signals(self):
        self.playlist_manager.current_item_changed.connect(self._on_track_changed)
        self.media_controller.playback_status_changed.connect(self._on_playback_status_changed)
        self.media_controller.position_changed.connect(self._on_position_changed)
        self.media_controller.duration_changed.connect(self._on_duration_changed)

    def _update_screen_combo(self):
        self.screen_combo.clear()
        screens = self.screen_manager.get_available_screens()
        for i, s in enumerate(screens):
            self.screen_combo.addItem(f"{i}: {s.name()}", i)
        
        idx = 1 if len(screens) > 1 else 0
        self.screen_combo.setCurrentIndex(idx)
        self.screen_manager.set_presentation_screen(idx)

    def _on_screen_selection_changed(self, index):
        if index >= 0: self.screen_manager.set_presentation_screen(self.screen_combo.itemData(index))

    def _toggle_timer(self):
        if self.is_timer_running:
            self.presentation_timer.stop()
            self.timer_btn.setText("Start Timer")
        else:
            self.presentation_timer.start(1000)
            self.timer_btn.setText("Pause Timer")
        self.is_timer_running = not self.is_timer_running

    def _reset_timer(self):
        self.presentation_timer.stop()
        self.elapsed_time = QTime(0, 0, 0)
        self.timer_label.setText("00:00:00")
        self.is_timer_running = False
        self.timer_btn.setText("Start Timer")

    def _update_timer(self):
        self.elapsed_time = self.elapsed_time.addSecs(1)
        self.timer_label.setText(self.elapsed_time.toString("HH:mm:ss"))

    def _toggle_black_screen(self):
        if self.presentation_window:
            is_black = self.black_btn.text() == "Black Screen"
            self.presentation_window.set_black_screen(is_black)
            self.black_btn.setText("Show Content" if is_black else "Black Screen")
            self.black_btn.setStyleSheet("background-color: red; color: white;" if is_black else "")

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Media", "", "Media (*.mp4 *.mov *.mkv *.jpg *.png);;All (*)")
        if files: self._process_added_files(files)

    def _process_added_files(self, files):
        for f in files:
            if not os.path.exists(f): continue
            self.playlist_manager.add_file(f)
            item = QListWidgetItem(os.path.basename(f))
            item.setData(Qt.ItemDataRole.UserRole, f)
            thumb = ThumbnailGenerator.generate(f, size=(64, 64))
            if not thumb.isNull(): item.setIcon(QIcon(thumb))
            self.playlist_view.addItem(item)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls() if u.toLocalFile().lower().endswith(('.mp4','.mov','.mkv','.jpg','.png','.avi'))]
        if files:
            self._process_added_files(files)
            e.acceptProposedAction()

    def _on_playlist_item_dbl_click(self, item):
        self.playlist_manager.set_current_index(self.playlist_view.row(item))

    def _toggle_presentation_screen(self):
        if not self.presentation_window:
            self.presentation_window = PresentationWindow()
            screen = self.screen_manager.get_presentation_screen_geometry()
            if screen: self.presentation_window.setGeometry(screen)
            self.presentation_window.showFullScreen()
            self.media_controller.set_window_id(self.presentation_window.get_video_container_id())
            self.screen_selector_btn.setText("Stop Presentation")
        else:
            self.presentation_window.close()
            self.presentation_window = None
            self.screen_selector_btn.setText("Start Presentation")
            self.media_controller.set_window_id(None)

    def _stop_playback(self): self.media_controller.stop()
    def _prev_track(self): self.playlist_manager.previous()
    def _next_track(self): self.playlist_manager.next()
    def _toggle_play(self): self.media_controller.toggle_pause()

    def _on_track_changed(self, item):
        if not item: return
        
        # Reset Seek
        self.duration = 0
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setValue(0)
        self.time_current_label.setText("00:00")
        self.time_total_label.setText("00:00")
        
        # Preview
        thumb = ThumbnailGenerator.generate(item.filepath, size=(800, 450))
        if not thumb.isNull():
            self.preview_label.setPixmap(thumb.scaled(self.current_preview_frame.size(), Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.preview_label.setText(f"Playing:\n{item.filename}")

        # Presentation Window
        if self.presentation_window:
            if self.media_controller.is_mock:
                if not thumb.isNull(): self.presentation_window.show_image(thumb)
                else: self.presentation_window.show_message(f"Playing:\n{item.filename}")
            else:
                self.presentation_window.clear_content()
                self.media_controller.set_window_id(self.presentation_window.get_video_container_id())
        else:
            if not self.media_controller.is_mock:
                self.media_controller.set_window_id(int(self.current_preview_frame.winId()))
        
        self.media_controller.load_file(item.filepath)
        self.setWindowTitle(f"ProVideoiPhoto - Playing: {item.filename}")

    def _on_playback_status_changed(self, is_playing):
        self.play_btn.setText("Pause" if is_playing else "Play")

    def _on_position_changed(self, pos):
        if self.duration <= 0:
            dur = self.media_controller.get_duration()
            if dur and dur > 0: self._on_duration_changed(dur)
        
        if not self.is_seeking:
            self.seek_slider.setValue(int(pos * 1000))
            self.time_current_label.setText(self._format_time(pos))

    def _on_duration_changed(self, dur):
        if not dur or dur <= 0: return
        self.duration = dur
        self.seek_slider.setRange(0, int(dur * 1000))
        self.time_total_label.setText(self._format_time(dur))

    def _on_seek_slider_pressed(self): self.is_seeking = True
    def _on_seek_slider_released(self):
        self.is_seeking = False
        self.media_controller.seek(self.seek_slider.value() / 1000.0)

    def _on_seek_slider_moved(self, pos):
        self.time_current_label.setText(self._format_time(pos / 1000.0))

    def _format_time(self, s):
        if not s: s = 0
        return f"{int(s // 60):02d}:{int(s % 60):02d}"
