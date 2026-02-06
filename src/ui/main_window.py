from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QSplitter, QFrame, QFileDialog, 
                               QListWidget, QListWidgetItem, QComboBox, QSlider)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QTime, QSettings
from PyQt6.QtGui import QAction, QIcon, QPixmap, QShortcut, QKeySequence
import logging
import os

from src.ui.presentation_window import PresentationWindow
from src.utils.thumbnail_generator import ThumbnailGenerator
from src.ui.hotkeys_dialog import HotkeysDialog

logger = logging.getLogger(__name__)

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.position().x()) / self.width()
            val = round(val)
            self.setValue(int(val))
            # Trigger sliderPressed signal to pause updates if needed
            self.sliderPressed.emit()
            # We also need to emit sliderMoved for immediate feedback if desired
            self.sliderMoved.emit(int(val))

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Ensure we commit the seek on release
        self.sliderReleased.emit()

class MainWindow(QMainWindow):
    def __init__(self, media_controller, playlist_manager, screen_manager):
        super().__init__()
        self.media_controller = media_controller
        self.playlist_manager = playlist_manager
        self.screen_manager = screen_manager
        
        self.presentation_window = None
        
        # Settings and Hotkeys
        self.settings = QSettings("ProVideoiPhoto", "AppConfig")
        self.shortcuts = {} 
        self._init_hotkeys_data()
        
        # Timer state
        self.presentation_timer = QTimer()
        self.presentation_timer.timeout.connect(self._update_timer)
        self.elapsed_time = QTime(0, 0, 0)
        self.is_timer_running = False
        
        # Seek state
        self.is_seeking = False
        self.duration = 0
        
        self.setWindowTitle("ProVideoiPhoto - Control Panel")
        self.resize(1200, 800)
        self.setAcceptDrops(True)
        
        self._apply_theme()
        self._init_ui()
        self._connect_signals()
        self._apply_hotkeys()
        
        # Check for Mock Mode
        if self.media_controller.is_mock:
            QTimer.singleShot(500, self._show_mock_warning)

    def _show_mock_warning(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Video Engine Missing", 
                          "Could not load 'libmpv'.\n\n"
                          "Video playback will be simulated (static thumbnail).\n"
                          "To enable real 4K video playback:\n"
                          "1. Download libmpv (mpv-1.dll) from SourceForge.\n"
                          "2. Place it in the application folder.\n"
                          "3. Restart the application.")

    def _apply_theme(self):
        pass

    def _init_hotkeys_data(self):
        self.default_hotkeys = {
            "play_pause": "Space",
            "stop": "Esc",
            "prev_track": "Left",
            "next_track": "Right",
            "black_screen": "B",
            "toggle_presentation": "F5",
            "add_files": "Ctrl+O",
            "toggle_timer": "T",
            "reset_timer": "R",
            "help": "F1"
        }
        # Load from settings or use default
        # Note: QSettings in Python might return everything as strings or slightly different types, 
        # but dict usually works if saved as such.
        self.current_hotkeys = self.settings.value("hotkeys", self.default_hotkeys)
        if not isinstance(self.current_hotkeys, dict):
            self.current_hotkeys = self.default_hotkeys

        # Ensure all keys exist (in case of updates)
        for k, v in self.default_hotkeys.items():
            if k not in self.current_hotkeys:
                self.current_hotkeys[k] = v

    def _apply_hotkeys(self):
        # Clear existing shortcuts
        for s in self.shortcuts.values():
            s.setEnabled(False)
            s.setParent(None)
        self.shortcuts.clear()
        
        # Map actions to slots
        self.actions_map = {
            "play_pause": self._toggle_play,
            "stop": self._stop_playback,
            "prev_track": self._prev_track,
            "next_track": self._next_track,
            "black_screen": self._toggle_black_screen,
            "toggle_presentation": self._toggle_presentation_screen,
            "add_files": self._add_files,
            "toggle_timer": self._toggle_timer,
            "reset_timer": self._reset_timer,
            "help": self._show_help
        }
        
        for action_name, key_seq in self.current_hotkeys.items():
            if action_name in self.actions_map and key_seq:
                shortcut = QShortcut(QKeySequence(key_seq), self)
                shortcut.activated.connect(self.actions_map[action_name])
                self.shortcuts[action_name] = shortcut
                self._update_tooltip(action_name, key_seq)

    def _update_tooltip(self, action_name, key_seq):
        # Map action names to widgets to update tooltips
        widgets = {
            "play_pause": self.play_btn,
            "stop": self.stop_btn,
            "prev_track": self.prev_btn,
            "next_track": self.next_btn,
            "black_screen": self.black_btn,
            "toggle_presentation": self.screen_selector_btn,
            "add_files": self.add_file_btn,
            "toggle_timer": self.timer_btn,
            "reset_timer": self.reset_timer_btn,
            "help": self.help_btn
        }
        if action_name in widgets:
            btn = widgets[action_name]
            btn.setToolTip(f"Shortcut: {key_seq}")

    def _show_help(self):
        dialog = HotkeysDialog(self.current_hotkeys, self, readonly=True)
        dialog.exec()

    def _open_hotkeys_dialog(self):
        dialog = HotkeysDialog(self.current_hotkeys, self)
        if dialog.exec():
            self.current_hotkeys = dialog.get_hotkeys()
            self.settings.setValue("hotkeys", self.current_hotkeys)
            self._apply_hotkeys()

    def _init_ui(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 1. Top Bar (Screen Selection, Status)
        top_bar = QHBoxLayout()
        
        # Screen Selector Combo
        self.screen_combo = QComboBox()
        self.screen_combo.setMinimumWidth(200)
        self._update_screen_combo()
        self.screen_combo.currentIndexChanged.connect(self._on_screen_selection_changed)
        top_bar.addWidget(self.screen_combo)

        self.screen_selector_btn = QPushButton("Start Presentation")
        self.screen_selector_btn.clicked.connect(self._toggle_presentation_screen)
        top_bar.addWidget(self.screen_selector_btn)
        
        top_bar.addStretch()
        
        # Timer Display
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        top_bar.addWidget(self.timer_label)
        
        self.timer_btn = QPushButton("Start Timer")
        self.timer_btn.clicked.connect(self._toggle_timer)
        top_bar.addWidget(self.timer_btn)
        
        self.reset_timer_btn = QPushButton("Reset")
        self.reset_timer_btn.clicked.connect(self._reset_timer)
        top_bar.addWidget(self.reset_timer_btn)

        # Help Button
        self.help_btn = QPushButton("Help (F1)")
        self.help_btn.clicked.connect(self._show_help)
        top_bar.addWidget(self.help_btn)
        
        top_bar.addStretch()
        
        main_layout.addLayout(top_bar)
        
        # 2. Main Content (Splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)
        
        # Left Side: Playlist
        self.playlist_widget = QWidget()
        playlist_layout = QVBoxLayout(self.playlist_widget)
        playlist_layout.addWidget(QLabel("Playlist"))
        
        self.add_file_btn = QPushButton("Add Files")
        self.add_file_btn.clicked.connect(self._add_files)
        playlist_layout.addWidget(self.add_file_btn)
        
        # Playlist View
        self.playlist_view = QListWidget()
        self.playlist_view.itemDoubleClicked.connect(self._on_playlist_item_dbl_click)
        playlist_layout.addWidget(self.playlist_view)
        
        splitter.addWidget(self.playlist_widget)
        
        # Right Side: Previews and Controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        splitter.addWidget(right_panel)
        
        # Previews (Current and Next)
        previews_layout = QHBoxLayout()
        
        # Current Preview (Dashboard Player)
        self.current_preview_frame = QFrame()
        self.current_preview_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.current_preview_frame.setMinimumSize(400, 225) # 16:9 aspect
        self.current_preview_frame.setStyleSheet("background-color: black;")
        
        # Add layout and label to preview frame
        preview_layout = QVBoxLayout(self.current_preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_label = QLabel(self.current_preview_frame)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: gray; font-size: 14px;")
        self.preview_label.setText("No Media Selected")
        preview_layout.addWidget(self.preview_label)
        
        previews_layout.addWidget(self.current_preview_frame, 7)
        
        # Next Preview
        self.next_preview_frame = QFrame()
        self.next_preview_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.next_preview_frame.setMinimumSize(160, 90)
        self.next_preview_frame.setStyleSheet("background-color: #222;")
        previews_layout.addWidget(self.next_preview_frame, 3)
        
        right_layout.addLayout(previews_layout)
        
        # Seek Slider and Time
        seek_layout = QHBoxLayout()
        
        self.time_current_label = QLabel("00:00")
        self.time_current_label.setStyleSheet("color: #666;")
        seek_layout.addWidget(self.time_current_label)
        
        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderPressed.connect(self._on_seek_slider_pressed)
        self.seek_slider.sliderReleased.connect(self._on_seek_slider_released)
        self.seek_slider.sliderMoved.connect(self._on_seek_slider_moved)
        # Handle click-to-seek if needed, but sliderMoved covers drag
        seek_layout.addWidget(self.seek_slider)
        
        self.time_total_label = QLabel("00:00")
        self.time_total_label.setStyleSheet("color: #666;")
        seek_layout.addWidget(self.time_total_label)
        
        right_layout.addLayout(seek_layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Prev")
        self.play_btn = QPushButton("Play")
        self.stop_btn = QPushButton("Stop")
        self.next_btn = QPushButton("Next")
        self.black_btn = QPushButton("Black Screen")
        
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.next_btn)
        
        # Volume Slider
        controls_layout.addSpacing(20)
        volume_label = QLabel("Vol:")
        controls_layout.addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        controls_layout.addWidget(self.volume_slider)
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.black_btn)
        
        right_layout.addLayout(controls_layout)
        
        # Connect controls
        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop_playback)
        self.prev_btn.clicked.connect(self._prev_track)
        self.next_btn.clicked.connect(self._next_track)
        self.black_btn.clicked.connect(self._toggle_black_screen)
        
        # Set splitter sizes (30% playlist, 70% preview)
        splitter.setSizes([360, 840])

    def _connect_signals(self):
        self.playlist_manager.current_item_changed.connect(self._on_track_changed)
        self.media_controller.playback_status_changed.connect(self._on_playback_status_changed)
        self.media_controller.position_changed.connect(self._on_position_changed)
        self.media_controller.duration_changed.connect(self._on_duration_changed)
    
    def _update_screen_combo(self):
        self.screen_combo.clear()
        screens = self.screen_manager.get_available_screens()
        for i, screen in enumerate(screens):
            name = screen.name()
            # Try to get more info if possible, or just index
            self.screen_combo.addItem(f"{i}: {name}", i)
            
        # Select secondary if available, else primary
        if len(screens) > 1:
            self.screen_combo.setCurrentIndex(1)
            self.screen_manager.set_presentation_screen(1)
        else:
            self.screen_combo.setCurrentIndex(0)
            self.screen_manager.set_presentation_screen(0)

    def _on_screen_selection_changed(self, index):
        if index >= 0:
            screen_idx = self.screen_combo.itemData(index)
            self.screen_manager.set_presentation_screen(screen_idx)

    def _on_volume_changed(self, value):
        self.media_controller.set_volume(value)

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
            # Need to track state or just toggle.
            # For now, let's assume if button says "Black Screen" we turn it on.
            if self.black_btn.text() == "Black Screen":
                self.presentation_window.set_black_screen(True)
                self.black_btn.setText("Show Content")
                self.black_btn.setStyleSheet("background-color: red; color: white;")
            else:
                self.presentation_window.set_black_screen(False)
                self.black_btn.setText("Black Screen")
                self.black_btn.setStyleSheet("")

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Media Files", "", 
                                                "Media Files (*.mp4 *.mov *.mkv *.jpg *.png);;All Files (*)")
        if files:
            self._process_added_files(files)

    def _process_added_files(self, files):
        """Helper to add files to playlist (used by dialog and drag-and-drop)"""
        for f in files:
            # Basic validation
            if not os.path.exists(f):
                continue
                
            self.playlist_manager.add_file(f)
            
            # Create item with thumbnail
            item = QListWidgetItem(os.path.basename(f))
            # Store full path in user role data just in case, though playlist_manager tracks by index
            item.setData(Qt.ItemDataRole.UserRole, f) 
            
            thumb = ThumbnailGenerator.generate(f, size=(64, 64))
            if not thumb.isNull():
                item.setIcon(QIcon(thumb))
            
            self.playlist_view.addItem(item)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                # Filter for valid extensions if needed, or rely on internal logic
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.mp4', '.mov', '.mkv', '.jpg', '.png', '.jpeg', '.avi']:
                    files.append(file_path)
        
        if files:
            self._process_added_files(files)
            event.acceptProposedAction()

    def _on_playlist_item_dbl_click(self, item):
        row = self.playlist_view.row(item)
        self.playlist_manager.set_current_index(row)

    def _toggle_presentation_screen(self):
        if not self.presentation_window:
            self.presentation_window = PresentationWindow()
            
            # Determine which screen to use
            target_screen_index = self.screen_manager._presentation_screen_index
            screens = self.screen_manager.get_available_screens()
            
            # Default to secondary if not set
            if target_screen_index == -1:
                if len(screens) > 1:
                    target_screen_index = 1
                else:
                    target_screen_index = 0
                self.screen_manager.set_presentation_screen(target_screen_index)
            
            if 0 <= target_screen_index < len(screens):
                target_screen = screens[target_screen_index]
                self.presentation_window.setGeometry(target_screen.geometry())
            
            self.presentation_window.showFullScreen()
            
            # Connect the player to this window
            self.media_controller.set_window_id(self.presentation_window.get_video_container_id())
            
            # If playing, make sure we ensure playback continues/starts
            if self.media_controller.is_playing:
                 # Re-issuing play might be needed depending on MPV behavior when reparenting (though we aren't reparenting, just setting ID)
                 pass

            self.screen_selector_btn.setText("Stop Presentation")
        else:
            self.presentation_window.close()
            self.presentation_window = None
            self.screen_selector_btn.setText("Start Presentation")
            # Reset player window to None or local preview if implemented
            self.media_controller.set_window_id(None)
            
    def _stop_playback(self):
        logger.info("Stop button clicked")
        self.media_controller.stop()
        
    def _prev_track(self):
        logger.info("Prev button clicked")
        self.playlist_manager.previous()
        
    def _next_track(self):
        logger.info("Next button clicked")
        self.playlist_manager.next()

    def _toggle_play(self):
        logger.info("Play/Pause button clicked")
        self.media_controller.toggle_pause()

    def _on_track_changed(self, item):
        if item:
            logger.info(f"Track changed to: {item.filename}")
            
            # Reset seek state
            self.duration = 0
            self.seek_slider.setRange(0, 0)
            self.seek_slider.setValue(0)
            self.time_current_label.setText("00:00")
            self.time_total_label.setText("00:00")
            
            # Generate thumbnail for preview (works for both video and image now)
            thumb = ThumbnailGenerator.generate(item.filepath, size=(800, 450))
            
            # Update Local Preview (always show thumbnail or placeholder)
            if not thumb.isNull():
                self.preview_label.setPixmap(thumb.scaled(self.current_preview_frame.size(), 
                                                        Qt.AspectRatioMode.KeepAspectRatio, 
                                                        Qt.TransformationMode.SmoothTransformation))
            else:
                self.preview_label.setText(f"Playing:\n{item.filename}")

            # Decide where to play
            if self.presentation_window:
                # Play on Presentation Window
                if self.media_controller.is_mock:
                    if not thumb.isNull():
                        self.presentation_window.show_image(thumb)
                    else:
                        self.presentation_window.show_message(f"Playing:\n{item.filename}")
                else:
                    self.presentation_window.clear_content()
                    # Ensure wid is set to presentation window
                    self.media_controller.set_window_id(self.presentation_window.get_video_container_id())
            else:
                # Play in Dashboard Preview
                if not self.media_controller.is_mock:
                    # We need to render video into the preview_frame
                    # Note: We need to hide the label so video is visible behind it? 
                    # Or just rely on MPV drawing over. 
                    # Usually MPV draws on the window handle.
                    self.media_controller.set_window_id(int(self.current_preview_frame.winId()))
            
            # Load and play
            self.media_controller.load_file(item.filepath)
            self.setWindowTitle(f"ProVideoiPhoto - Playing: {item.filename}")
            

    def _on_playback_status_changed(self, is_playing):
        self.play_btn.setText("Pause" if is_playing else "Play")

    def _on_position_changed(self, position):
        # Safety check: if duration is missing, try to fetch it
        if self.duration <= 0:
            dur = self.media_controller.get_duration()
            if dur > 0:
                self._on_duration_changed(dur)

        if not self.is_seeking:
            # Slider uses milliseconds for better precision
            self.seek_slider.setValue(int(position * 1000))
            self.time_current_label.setText(self._format_time(position))

    def _on_duration_changed(self, duration):
        if duration is None or duration <= 0:
            return
        self.duration = duration
        # Set range in milliseconds
        self.seek_slider.setRange(0, int(duration * 1000))
        self.time_total_label.setText(self._format_time(duration))

    def _on_seek_slider_pressed(self):
        self.is_seeking = True

    def _on_seek_slider_released(self):
        self.is_seeking = False
        # Convert back from milliseconds
        target_pos = self.seek_slider.value() / 1000.0
        self.media_controller.seek(target_pos)

    def _on_seek_slider_moved(self, position):
        # Update label while dragging (convert ms to sec)
        self.time_current_label.setText(self._format_time(position / 1000.0))
        # Optional: Live seek
        # self.media_controller.seek(position / 1000.0)

    def _format_time(self, seconds):
        if seconds is None:
            seconds = 0
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
