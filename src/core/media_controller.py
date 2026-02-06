import logging
import os
import sys
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

# Add project root to PATH so python-mpv can find libmpv-2.dll
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
    # Also check the executable directory for the DLL
    exe_dir = os.path.dirname(sys.executable)
    if exe_dir not in os.environ["PATH"]:
        os.environ["PATH"] = exe_dir + os.pathsep + os.environ["PATH"]
else:
    # Running from source
    application_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if application_path not in os.environ["PATH"]:
    os.environ["PATH"] = application_path + os.pathsep + os.environ["PATH"]

# Try importing mpv, handle failure by defining a Mock class
try:
    import mpv
    MPV_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"MPV not available: {e}. Using Mock Player.")
    MPV_AVAILABLE = False
    mpv = None

class MockMPV:
    """Mock MPV class for development without libmpv"""
    def __init__(self, **kwargs):
        self.pause = False
        self.time_pos = 0.0
        self.duration = 100.0
        self.wid = None
        self.speed = 1.0
        self.volume = 100.0
        self._observers = {}
        
        # Simulate playback timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_time)
        self._timer.start(100) # 100ms update

    def _update_time(self):
        if not self.pause:
            self.time_pos += 0.1 * self.speed
            if self.time_pos > self.duration:
                self.time_pos = 0.0
            
            # Notify observers
            if 'time-pos' in self._observers:
                self._observers['time-pos']('time-pos', self.time_pos)

    def play(self, filepath):
        logger.info(f"[MockMPV] Playing {filepath}")
        self.time_pos = 0.0
        self.pause = False
        # Trigger duration update
        if 'duration' in self._observers:
            self._observers['duration']('duration', self.duration)

    def stop(self):
        logger.info("[MockMPV] Stop")
        self.pause = True
        self.time_pos = 0.0

    def seek(self, position, reference='absolute'):
        logger.info(f"[MockMPV] Seek to {position}")
        self.time_pos = position

    def property_observer(self, name):
        def decorator(func):
            self._observers[name] = func
            return func
        return decorator
    
    def wait_for_property(self, name):
        pass

class MediaController(QObject):
    position_changed = pyqtSignal(float)
    duration_changed = pyqtSignal(float)
    playback_status_changed = pyqtSignal(bool) # True for playing, False for paused
    
    def __init__(self):
        super().__init__()
        self.player = None
        self._initialize_player()

    def _initialize_player(self):
        if MPV_AVAILABLE:
            try:
                # Initialize MPV with hardware acceleration and professional settings
                self.player = mpv.MPV(
                    input_default_bindings=True,
                    input_vo_keyboard=True,
                    osc=True,
                    vo='gpu',
                    hwdec='auto',
                    keep_open='yes'
                )
                self._setup_observers()
                logger.info("MediaController initialized successfully with HW acceleration")
            except Exception as e:
                logger.error(f"Failed to initialize MPV: {e}")
                self._use_mock()
        else:
            self._use_mock()

    def _use_mock(self):
        logger.info("Initializing Mock Player")
        self.player = MockMPV()
        self._setup_observers()
        
    @property
    def is_mock(self):
        return isinstance(self.player, MockMPV)

    def _setup_observers(self):
        # Connect property observers
        @self.player.property_observer('time-pos')
        def on_time_pos(name, value):
            if value is not None:
                self.position_changed.emit(value)
                
        @self.player.property_observer('duration')
        def on_duration(name, value):
            if value is not None:
                self.duration_changed.emit(value)

    def set_window_id(self, wid):
        if self.player:
            # Handle MockMPV separately if needed, but it has .wid attribute too
            if MPV_AVAILABLE and isinstance(self.player, mpv.MPV):
                try:
                    if wid is None:
                        # mpv property 'wid' requires an integer handle or special logic to detach.
                        # Setting to 0 or a dummy value might be safer, or just ignoring if we can't detach.
                        # Usually 0 means "no window" or "detach" depending on backend.
                        # BUT python-mpv might expect an int.
                        # Let's try setting to 0 if None passed, as None is not a valid property value for 'wid' usually.
                        self.player.wid = 0 
                    else:
                        self.player.wid = wid
                except (mpv.ShutdownError, OSError) as e:
                    logger.error(f"MPV Core shutdown unexpectedly: {e}. Attempting to re-initialize.")
                    try:
                        # Clean up old player if possible (though it's shutdown)
                        if hasattr(self.player, 'terminate'):
                            try: self.player.terminate() 
                            except: pass
                        
                        self._initialize_player()
                        
                        # Try setting wid again on new player
                        if self.player and isinstance(self.player, mpv.MPV):
                            self.player.wid = wid if wid is not None else 0
                    except Exception as reinit_error:
                        logger.error(f"Failed to recover MPV player: {reinit_error}")
                        self._use_mock()

            else:
                self.player.wid = wid

    def load_file(self, filepath):
        if not self.player:
            logger.error("Player not initialized")
            return False
            
        try:
            # Check if we have a window ID set. If not, MPV might spawn a standalone window.
            # However, in main_window.py we now ensure wid is set to either presentation or preview frame.
            # Just to be safe, if no wid is set and we are not mock, we might want to avoid playing or default to dummy.
            if MPV_AVAILABLE and isinstance(self.player, mpv.MPV):
                 if self.player.wid is None:
                     logger.warning("No window ID set for MPV. Playback might open a new window or fail.")
                     # self.player.vo = 'null' # Could disable video output if needed
            
            self.player.play(filepath)
            # Removed blocking wait: self.player.wait_for_property('duration')
            # The duration will be updated via the property observer asynchronously.
            self.playback_status_changed.emit(True)
            logger.info(f"Started playback for: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading file {filepath}: {e}")
            return False

    def _safe_exec(self, func_name, *args, **kwargs):
        """Execute a player command safely, recovering if the core is shutdown."""
        if not self.player:
            return None
            
        if MPV_AVAILABLE and isinstance(self.player, mpv.MPV):
            try:
                # Try to access/call the attribute
                attr = getattr(self.player, func_name)
                # If it's a property, we might need to set it, but this helper is mostly for methods or getting
                # However, for simple property access like self.player.pause = x, we can't use this easily 
                # without changing the call site structure.
                # So we will wrap the specific methods instead.
                pass
            except (mpv.ShutdownError, OSError):
                logger.error(f"MPV Core shutdown detected during {func_name}. Re-initializing.")
                self._initialize_player()
                # Try again? Depends on the action.
                return None
        return None

    def play(self):
        if self.player:
            try:
                self.player.pause = False
                self.playback_status_changed.emit(True)
            except (mpv.ShutdownError, OSError):
                self._handle_crash()

    def pause(self):
        if self.player:
            try:
                self.player.pause = True
                self.playback_status_changed.emit(False)
            except (mpv.ShutdownError, OSError):
                self._handle_crash()

    def toggle_pause(self):
        if self.player:
            try:
                self.player.pause = not self.player.pause
                self.playback_status_changed.emit(not self.player.pause)
            except (mpv.ShutdownError, OSError):
                logger.error("MPV Core shutdown during toggle_pause.")
                self._handle_crash()

    def stop(self):
        if self.player:
            try:
                self.player.stop()
                self.playback_status_changed.emit(False)
            except (mpv.ShutdownError, OSError):
                self._handle_crash()

    def seek(self, position):
        if self.player:
            try:
                self.player.seek(position, reference='absolute')
            except (mpv.ShutdownError, OSError):
                self._handle_crash()

    def set_speed(self, speed):
        if self.player:
            try:
                self.player.speed = speed
            except (mpv.ShutdownError, OSError):
                self._handle_crash()

    def set_volume(self, volume):
        """Set volume (0-100)"""
        if self.player:
            try:
                self.player.volume = volume
            except (mpv.ShutdownError, OSError):
                self._handle_crash()

    def _handle_crash(self):
        """Attempt to recover from a crash"""
        logger.error("Attempting to recover MPV player from crash...")
        try:
            if hasattr(self.player, 'terminate'):
                try: self.player.terminate() 
                except: pass
            self._initialize_player()
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            self._use_mock()

    def get_volume(self):
        if self.player:
            try:
                return self.player.volume
            except (mpv.ShutdownError, OSError):
                return 100
        return 100

    def get_duration(self):
        if self.player:
            try:
                return self.player.duration
            except (mpv.ShutdownError, OSError):
                return 0.0
        return 0.0

    def get_position(self):
        if self.player:
            try:
                return self.player.time_pos
            except (mpv.ShutdownError, OSError):
                return 0.0
        return 0.0

    @property
    def is_playing(self):
        if self.player:
            try:
                return not self.player.pause
            except (mpv.ShutdownError, OSError):
                return False
        return False
