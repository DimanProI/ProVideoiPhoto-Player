import logging
import os
import sys
import ctypes
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

# Register DLL Paths
if getattr(sys, 'frozen', False):
    # Compiled Mode
    if hasattr(sys, '_MEIPASS'):
        app_path = sys._MEIPASS
    else:
        app_path = os.path.dirname(sys.executable)
    
    exe_dir = os.path.dirname(sys.executable)
    search_paths = [app_path, exe_dir]
    
    # Python 3.8+ DLL Loading
    if hasattr(os, 'add_dll_directory'):
        for p in search_paths:
            try: os.add_dll_directory(p)
            except: pass

    # Update PATH
    sep = ';' if os.name == 'nt' else ':'
    os.environ["PATH"] = sep.join(search_paths) + sep + os.environ["PATH"]
else:
    # Source Mode
    app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if hasattr(os, 'add_dll_directory'):
        try: os.add_dll_directory(app_path)
        except: pass
    os.environ["PATH"] = app_path + os.pathsep + os.environ["PATH"]

# Pre-load DLLs to assist python-mpv
for name in ['libmpv-2.dll', 'mpv-1.dll', 'mpv-2.dll']:
    try:
        path = os.path.join(app_path, name)
        if os.path.exists(path):
            ctypes.CDLL(path)
            break
        if getattr(sys, 'frozen', False):
            path = os.path.join(exe_dir, name)
            if os.path.exists(path):
                ctypes.CDLL(path)
                break
    except: pass

# Import MPV or Mock
try:
    import mpv
    MPV_AVAILABLE = True
except (ImportError, OSError, FileNotFoundError):
    MPV_AVAILABLE = False
    mpv = None

class MockMPV:
    """Simulates MPV behavior when libmpv is missing."""
    def __init__(self, **kwargs):
        self.pause = False
        self.time_pos = 0.0
        self.duration = 100.0
        self.wid = None
        self.speed = 1.0
        self.volume = 100.0
        self._observers = {}
        
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_time)
        self._timer.start(100)

    def _update_time(self):
        if not self.pause:
            self.time_pos += 0.1 * self.speed
            if self.time_pos > self.duration: self.time_pos = 0.0
            if 'time-pos' in self._observers:
                self._observers['time-pos']('time-pos', self.time_pos)

    def play(self, filepath):
        self.time_pos = 0.0
        self.pause = False
        if 'duration' in self._observers:
            self._observers['duration']('duration', self.duration)

    def stop(self):
        self.pause = True
        self.time_pos = 0.0

    def seek(self, position, reference='absolute'):
        self.time_pos = position

    def property_observer(self, name):
        def decorator(func):
            self._observers[name] = func
            return func
        return decorator

class MediaController(QObject):
    position_changed = pyqtSignal(float)
    duration_changed = pyqtSignal(float)
    playback_status_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.player = None
        self._initialize_player()

    def _initialize_player(self):
        if MPV_AVAILABLE:
            try:
                self.player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True, vo='gpu', hwdec='auto', keep_open='yes')
                self._setup_observers()
            except Exception:
                self._use_mock()
        else:
            self._use_mock()

    def _use_mock(self):
        self.player = MockMPV()
        self._setup_observers()
        
    @property
    def is_mock(self):
        return isinstance(self.player, MockMPV)

    def _setup_observers(self):
        @self.player.property_observer('time-pos')
        def on_time_pos(name, value):
            if value is not None: self.position_changed.emit(value)
                
        @self.player.property_observer('duration')
        def on_duration(name, value):
            if value is not None: self.duration_changed.emit(value)

    def set_window_id(self, wid):
        if self.player:
            try:
                if MPV_AVAILABLE and isinstance(self.player, mpv.MPV):
                    self.player.wid = wid if wid is not None else 0
                else:
                    self.player.wid = wid
            except:
                self._initialize_player()

    def load_file(self, filepath):
        if not self.player: return False
        try:
            self.player.play(filepath)
            self.playback_status_changed.emit(True)
            return True
        except: return False

    def play(self):
        self._exec_cmd(lambda: setattr(self.player, 'pause', False))
        self.playback_status_changed.emit(True)

    def pause(self):
        self._exec_cmd(lambda: setattr(self.player, 'pause', True))
        self.playback_status_changed.emit(False)

    def toggle_pause(self):
        if self.player:
            self._exec_cmd(lambda: setattr(self.player, 'pause', not self.player.pause))
            self.playback_status_changed.emit(not self.player.pause)

    def stop(self):
        self._exec_cmd(lambda: self.player.stop())
        self.playback_status_changed.emit(False)

    def seek(self, position):
        self._exec_cmd(lambda: self.player.seek(position, reference='absolute'))

    def set_volume(self, volume):
        self._exec_cmd(lambda: setattr(self.player, 'volume', volume))

    def get_duration(self):
        val = self._get_prop('duration', 0.0)
        return val if val is not None else 0.0

    def get_position(self):
        val = self._get_prop('time_pos', 0.0)
        return val if val is not None else 0.0

    @property
    def is_playing(self):
        if not self.player: return False
        try: return not self.player.pause
        except: return False

    def _exec_cmd(self, func):
        if self.player:
            try: func()
            except: self._handle_crash()

    def _get_prop(self, prop, default):
        if self.player:
            try: return getattr(self.player, prop)
            except: return default
        return default

    def _handle_crash(self):
        try:
            if hasattr(self.player, 'terminate'): self.player.terminate()
            self._initialize_player()
        except: self._use_mock()
