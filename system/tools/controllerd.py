#!/usr/bin/env python3
"""
Controller Mapper Daemon for Batocera Firefox
Loads profiles from profiles/ directory and accepts commands via FIFO

Commands via FIFO (/run/controllerd.cmd):
  profile <name>  - Load profile from profiles/<name>.cfg
  stop            - Stop the daemon
  reload          - Reload current profile
  list            - List available profiles
"""

from evdev import InputDevice, UInput, ecodes
import math
import time
import select
import os
import sys
import configparser
import signal
import fcntl
import glob
import subprocess

# Configuration paths
PROFILES_DIR = 'profiles'
FIFO_PATH = '/run/controllerd.cmd'
PIDFILE_PATH = '/run/controllerd.pid'

# Default configuration
DEFAULT_CONFIG = {
    'mouse': {
        'enabled': 'false',
        'tick_rate': '10',
        'deadzone': '0.12',
        'sensitivity': '9.0',
    },
    'scroll': {
        'enabled': 'false',
        'deadzone': '0.15',
        'sensitivity': '5.0',
    },
    'bindings': {
    },
    'dpad': {
        'enabled': 'false',
    },
    'debug': {
        'enabled': 'false',
    },
}

# Button name to evdev code mapping
BUTTON_MAP = {
    # Controller buttons
    'BTN_SOUTH': ecodes.BTN_SOUTH,      # X (PlayStation)
    'BTN_EAST': ecodes.BTN_EAST,        # B (Xbox) / Circle (PlayStation)
    'BTN_NORTH': ecodes.BTN_NORTH,      # Y (Xbox) / Triangle (PlayStation)
    'BTN_WEST': ecodes.BTN_WEST,        # A (Xbox) / Square (PlayStation)
    'BTN_TL': ecodes.BTN_TL,            # L1
    'BTN_TR': ecodes.BTN_TR,            # R1
    'BTN_TL2': ecodes.BTN_TL2,          # L2
    'BTN_TR2': ecodes.BTN_TR2,          # R2
    'BTN_SELECT': ecodes.BTN_SELECT,    # Share / Back / Select
    'BTN_START': ecodes.BTN_START,      # Options / Start
    'BTN_MODE': ecodes.BTN_MODE,        # PS / Xbox / Home
    'BTN_THUMBL': ecodes.BTN_THUMBL,    # L3
    'BTN_THUMBR': ecodes.BTN_THUMBR,    # R3
    # Mouse/Keyboard outputs
    'BTN_LEFT': ecodes.BTN_LEFT,
    'BTN_RIGHT': ecodes.BTN_RIGHT,
    'BTN_MIDDLE': ecodes.BTN_MIDDLE,
    'BTN_SIDE': ecodes.BTN_SIDE,
    'BTN_EXTRA': ecodes.BTN_EXTRA,
    'KEY_UP': ecodes.KEY_UP,
    'KEY_DOWN': ecodes.KEY_DOWN,
    'KEY_LEFT': ecodes.KEY_LEFT,
    'KEY_RIGHT': ecodes.KEY_RIGHT,
    'KEY_ENTER': ecodes.KEY_ENTER,
    'KEY_ESC': ecodes.KEY_ESC,
    'KEY_SPACE': ecodes.KEY_SPACE,
    'KEY_TAB': ecodes.KEY_TAB,
    'KEY_PAGEUP': ecodes.KEY_PAGEUP,
    'KEY_PAGEDOWN': ecodes.KEY_PAGEDOWN,
    'KEY_HOME': ecodes.KEY_HOME,
    'KEY_END': ecodes.KEY_END,
    'KEY_BACKSPACE': ecodes.KEY_BACKSPACE,
    'KEY_DELETE': ecodes.KEY_DELETE,
    'KEY_F5': ecodes.KEY_F5,
}

# Reverse mapping for debug output
BUTTON_NAMES = {v: k for k, v in BUTTON_MAP.items()}


class ControllerDaemon:
    """Daemon that manages controller input and responds to FIFO commands."""
    
    def __init__(self):
        self.running = False
        self.fifo_fd = None
        self.dev = None
        self.ui = None
        self.config = None
        self.bindings = {}
        self.mouse_enabled = True
        self.tick_rate = 0.1
        self.deadzone = 0.12
        self.sensitivity = 9.0
        self.dpad_enabled = True
        self.debug_enabled = False
        self.current_profile = None
        
        # Stick state
        self.center_x = 0
        self.center_y = 0
        self.range_x = 1
        self.range_y = 1
        self.rx = 0
        self.ry = 0
        self.acc_x = 0.0
        self.acc_y = 0.0
        self.dpad_state = (0, 0)
        self.last_tick = time.monotonic()
        
        # Hotkey combo state (PS + Start to close app)
        self.pressed_buttons = set()
        self._hotkey_triggered = False
        self._hotkey_cooldown = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
    
    def _create_fifo(self):
        """Create the FIFO pipe for commands."""
        # Remove existing FIFO if present
        if os.path.exists(FIFO_PATH):
            os.remove(FIFO_PATH)
        
        # Create new FIFO
        os.mkfifo(FIFO_PATH, 0o666)
        print(f"Created FIFO: {FIFO_PATH}")
        
        # Open in non-blocking mode for reading
        self.fifo_fd = os.open(FIFO_PATH, os.O_RDONLY | os.O_NONBLOCK)
    
    def _cleanup_fifo(self):
        """Clean up the FIFO pipe."""
        if self.fifo_fd is not None:
            os.close(self.fifo_fd)
            self.fifo_fd = None
        if os.path.exists(FIFO_PATH):
            os.remove(FIFO_PATH)
            print(f"Removed FIFO: {FIFO_PATH}")
    
    def _write_pidfile(self):
        """Write PID file."""
        with open(PIDFILE_PATH, 'w') as f:
            f.write(str(os.getpid()))
        print(f"PID file: {PIDFILE_PATH}")
    
    def _remove_pidfile(self):
        """Remove PID file."""
        if os.path.exists(PIDFILE_PATH):
            os.remove(PIDFILE_PATH)
    
    def list_profiles(self):
        """List all available profiles."""
        profiles = []
        pattern = os.path.join(PROFILES_DIR, '*.cfg')
        for path in glob.glob(pattern):
            name = os.path.basename(path)[:-4]  # Remove .cfg extension
            profiles.append(name)
        return sorted(profiles)
    
    def load_config(self, profile_name):
        """Load configuration from a profile."""
        profile_path = os.path.join(PROFILES_DIR, f"{profile_name}.cfg")
        
        config = configparser.ConfigParser()
        
        # Load from file first (if exists)
        if os.path.exists(profile_path):
            print(f"Loading profile: {profile_path}")
            config.read(profile_path)
            self.current_profile = profile_name
        else:
            print(f"Profile not found: {profile_path}, using defaults")
            self.current_profile = None
        
        # Apply defaults only for missing sections/keys
        for section, values in DEFAULT_CONFIG.items():
            if section not in config:
                config[section] = values.copy()
            else:
                # Section exists, fill in missing keys with defaults
                for key, value in values.items():
                    if key not in config[section]:
                        config[section][key] = value
        
        self.config = config
        return config
    
    def parse_bindings(self):
        """Parse button bindings from config."""
        bindings = {}
        
        if 'bindings' not in self.config.sections():
            return bindings
        
        for btn_name, action_name in self.config['bindings'].items():
            btn_name = btn_name.upper()
            action_name = action_name.upper()
            
            if btn_name in BUTTON_MAP and action_name in BUTTON_MAP:
                bindings[BUTTON_MAP[btn_name]] = BUTTON_MAP[action_name]
            else:
                print(f"Warning: Unknown binding '{btn_name}' -> '{action_name}'")
        
        self.bindings = bindings
        return bindings
    
    def setup_device(self):
        """Setup the input device."""
        device_path = self.config.get('device', 'path', fallback='/dev/input/event16')
        
        # Close existing device if any
        if self.dev is not None:
            try:
                self.dev.ungrab()
            except:
                pass
            self.dev = None
        
        print(f"Opening device: {device_path}")
        self.dev = InputDevice(device_path)
        
        # Set non-blocking mode
        fd = self.dev.fd
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        # Remember device identity for reconnection
        self._original_device_path = device_path
        self._device_name = self.dev.name
        print(f"Connected to '{self._device_name}' at {device_path}")
        
        return self.dev
    
    def setup_mouse_params(self):
        """Setup mouse parameters from config."""
        self.mouse_enabled = self.config.getboolean('mouse', 'enabled', fallback=True)
        self.tick_rate = 1.0 / self.config.getfloat('mouse', 'tick_rate', fallback=50.0)
        self.deadzone = self.config.getfloat('mouse', 'deadzone', fallback=0.12)
        self.sensitivity = self.config.getfloat('mouse', 'sensitivity', fallback=9.0)
        
        status = "enabled" if self.mouse_enabled else "disabled"
        print(f"Mouse {status}: tick_rate={1.0/self.tick_rate:.0f}Hz, deadzone={self.deadzone}, sens={self.sensitivity}")
    
    def get_capabilities(self):
        """Build capabilities dict for UInput."""
        caps = {
            ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y],
            ecodes.EV_KEY: [],
        }
        
        # Add all output keys from bindings
        for action_code in self.bindings.values():
            if action_code not in caps[ecodes.EV_KEY]:
                caps[ecodes.EV_KEY].append(action_code)
        
        # Always add mouse buttons and arrow keys for D-pad
        for code in [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_SIDE, ecodes.BTN_EXTRA,
                     ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_LEFT, ecodes.KEY_RIGHT]:
            if code not in caps[ecodes.EV_KEY]:
                caps[ecodes.EV_KEY].append(code)
        
        return caps
    
    def setup_uinput(self):
        """Setup virtual input device."""
        # Close existing uinput if any
        if self.ui is not None:
            self.ui.close()
            self.ui = None
        
        caps = self.get_capabilities()
        profile_name = self.current_profile or "default"
        self.ui = UInput(caps, name=f"Controller Mapper ({profile_name})")
        return self.ui
    
    def stick_vector(self, x, y):
        """Convert stick position to normalized vector."""
        nx = (x - self.center_x) / self.range_x
        ny = (y - self.center_y) / self.range_y

        mag = math.hypot(nx, ny)
        if mag < self.deadzone:
            return 0.0, 0.0

        scale = (mag - self.deadzone) / (1.0 - self.deadzone)
        nx = (nx / mag) * scale
        ny = (ny / mag) * scale

        return nx * self.sensitivity, ny * self.sensitivity
    
    def update_dpad_keys(self, new_x, new_y):
        """Update D-pad key states."""
        changed = False
        dpad_x, dpad_y = self.dpad_state

        # Handle X axis (left/right)
        if new_x != dpad_x:
            if dpad_x == -1:
                self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFT, 0)
                changed = True
            elif dpad_x == 1:
                self.ui.write(ecodes.EV_KEY, ecodes.KEY_RIGHT, 0)
                changed = True

            if new_x == -1:
                self.ui.write(ecodes.EV_KEY, ecodes.KEY_LEFT, 1)
                changed = True
            elif new_x == 1:
                self.ui.write(ecodes.EV_KEY, ecodes.KEY_RIGHT, 1)
                changed = True

            dpad_x = new_x

        # Handle Y axis (up/down)
        if new_y != dpad_y:
            if dpad_y == -1:
                self.ui.write(ecodes.EV_KEY, ecodes.KEY_UP, 0)
                changed = True
            elif dpad_y == 1:
                self.ui.write(ecodes.EV_KEY, ecodes.KEY_DOWN, 0)
                changed = True

            if new_y == -1:
                self.ui.write(ecodes.EV_KEY, ecodes.KEY_UP, 1)
                changed = True
            elif new_y == 1:
                self.ui.write(ecodes.EV_KEY, ecodes.KEY_DOWN, 1)
                changed = True

            dpad_y = new_y

        if changed:
            self.ui.syn()

        self.dpad_state = (dpad_x, dpad_y)
    
    def _device_disconnected(self):
        """Handle device disconnection."""
        print("Controller disconnected!")
        if self.dev is not None:
            try:
                self.dev.ungrab()
            except:
                pass
            self.dev = None
        self._release_all_keys()

    def _release_all_keys(self):
        """Release all pressed keys and reset stick state."""
        if self.ui is None:
            return
        try:
            for code in self.bindings.values():
                self.ui.write(ecodes.EV_KEY, code, 0)
            for code in [ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_LEFT, ecodes.KEY_RIGHT,
                         ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_SIDE, ecodes.BTN_EXTRA]:
                self.ui.write(ecodes.EV_KEY, code, 0)
            self.ui.write(ecodes.EV_REL, ecodes.REL_X, 0)
            self.ui.write(ecodes.EV_REL, ecodes.REL_Y, 0)
            self.ui.syn()
        except:
            pass
        self.acc_x = 0.0
        self.acc_y = 0.0
        self.dpad_state = (0, 0)
        # Reset hotkey combo state
        self.pressed_buttons.clear()
        self._hotkey_triggered = False

    def _check_hotkey_combo(self, btn_code, pressed):
        """Check for PS + Start hotkey combo to close app.
        
        When both BTN_MODE (PS) and BTN_START are pressed simultaneously,
        kill the running Firefox process to exit kiosk mode."""
        if pressed:
            self.pressed_buttons.add(btn_code)
        else:
            self.pressed_buttons.discard(btn_code)
            # Any release resets the triggered flag
            self._hotkey_triggered = False

        # Check if combo is active (both PS and Start pressed)
        if (ecodes.BTN_MODE in self.pressed_buttons and 
            ecodes.BTN_START in self.pressed_buttons and
            not self._hotkey_triggered):
            
            now = time.monotonic()
            # Cooldown: prevent multiple triggers within 2 seconds
            if now - self._hotkey_cooldown < 2.0:
                return
            
            self._hotkey_triggered = True
            self._hotkey_cooldown = now
            print("[HOTKEY] PS + Start combo detected — closing app")
            self._close_app()

    def _close_app(self):
        """Close the running app by killing Firefox processes."""
        try:
            # Release all keys first to prevent stuck inputs
            self._release_all_keys()
            
            # Kill all Firefox processes
            # This will cause the ROM script's 'wait $FF_PID' to return,
            # which then sends 'profile disabled'
            subprocess.Popen(
                ['pkill', '-f', 'firefox'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("[HOTKEY] Sent kill signal to Firefox processes")
        except Exception as e:
            print(f"[HOTKEY] Error closing app: {e}")

    def _find_controller_device(self):
        """Find controller device by scanning /dev/input/ devices.
        
        If the original device path still exists, use it.
        Otherwise, search by device name matching the previously connected device.
        Returns device path or None."""
        if not hasattr(self, '_original_device_path') or not self._original_device_path:
            return None

        # Try original path first
        if os.path.exists(self._original_device_path):
            return self._original_device_path

        # Try to find by name
        target_name = getattr(self, '_device_name', None)
        if target_name:
            for path in sorted(glob.glob('/dev/input/event*')):
                try:
                    dev = InputDevice(path)
                    if target_name.lower() in dev.name.lower() or dev.name.lower() in target_name.lower():
                        dev.close()
                        print(f"Found controller '{target_name}' at {path}")
                        return path
                    dev.close()
                except:
                    continue

        # Last resort: find any device with ABS_RX capability (right stick)
        for path in sorted(glob.glob('/dev/input/event*')):
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                if ecodes.EV_ABS in caps:
                    abs_codes = [c[0] if isinstance(c, tuple) else c for c in caps[ecodes.EV_ABS]]
                    if ecodes.ABS_RX in abs_codes and ecodes.ABS_RY in abs_codes:
                        print(f"Found controller-like device at {path}: {dev.name}")
                        dev.close()
                        return path
                dev.close()
            except:
                continue

        return None

    def _try_reconnect(self):
        """Try to reconnect to the controller."""
        device_path = self._find_controller_device()
        if device_path is None:
            return False

        print(f"Attempting reconnect at {device_path}")
        try:
            self.dev = InputDevice(device_path)
            fd = self.dev.fd
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

            abs_rx = self.dev.absinfo(ecodes.ABS_RX)
            abs_ry = self.dev.absinfo(ecodes.ABS_RY)

            self.center_x = (abs_rx.max + abs_rx.min) / 2.0
            self.center_y = (abs_ry.max + abs_ry.min) / 2.0
            self.range_x = (abs_rx.max - abs_rx.min) / 2.0
            self.range_y = (abs_ry.max - abs_ry.min) / 2.0

            self.rx = self.center_x
            self.ry = self.center_y
            self.acc_x = 0.0
            self.acc_y = 0.0
            self.dpad_state = (0, 0)

            # Reset hotkey combo state for clean reconnection
            self.pressed_buttons.clear()
            self._hotkey_triggered = False

            self._device_name = self.dev.name
            self._original_device_path = device_path
            print(f"Reconnected to '{self._device_name}' at {device_path}")
            return True
        except Exception as e:
            print(f"Reconnect failed: {e}")
            self.dev = None
            return False

    def process_events(self):
        """Process all pending input events."""
        try:
            while True:
                r, _, _ = select.select([self.dev.fd], [], [], 0)
                if not r:
                    break

                for e in self.dev.read():
                    if e.type == ecodes.EV_ABS:
                        if e.code == ecodes.ABS_RX:
                            self.rx = e.value
                        elif e.code == ecodes.ABS_RY:
                            self.ry = e.value
                        elif self.dpad_enabled and e.code == ecodes.ABS_HAT0X:
                            self.update_dpad_keys(e.value, self.dpad_state[1])
                        elif self.dpad_enabled and e.code == ecodes.ABS_HAT0Y:
                            self.update_dpad_keys(self.dpad_state[0], e.value)

                    elif e.type == ecodes.EV_KEY:
                        if self.debug_enabled and e.code in BUTTON_NAMES:
                            btn_name = BUTTON_NAMES[e.code]
                            state = "PRESSED" if e.value == 1 else "RELEASED" if e.value == 0 else "REPEAT"
                            print(f"[DEBUG] Button {btn_name} {state}")

                        # Track button state for hotkey combo detection
                        if e.value in (1, 0):  # press or release (not repeat)
                            self._check_hotkey_combo(e.code, e.value == 1)

                        # Only map buttons if hotkey combo is not active
                        if ecodes.BTN_MODE not in self.pressed_buttons or ecodes.BTN_START not in self.pressed_buttons:
                            if e.code in self.bindings:
                                action_code = self.bindings[e.code]
                                self.ui.write(ecodes.EV_KEY, action_code, e.value)
                                self.ui.syn()

                                if self.debug_enabled and action_code in BUTTON_NAMES:
                                    print(f"[DEBUG] -> Emitted {BUTTON_NAMES[action_code]}")
        except BlockingIOError:
            pass
        except (OSError, IOError):
            print("Device read error - controller may have disconnected")
            self._device_disconnected()
        except Exception as e:
            if 'Resource temporarily unavailable' in str(e):
                pass
            else:
                print(f"Unexpected error reading device: {e}")
                self._device_disconnected()
    
    def update_mouse(self):
        """Update mouse movement."""
        if not self.mouse_enabled:
            return
            
        now = time.monotonic()
        if now - self.last_tick >= self.tick_rate:
            self.last_tick = now

            dx_f, dy_f = self.stick_vector(self.rx, self.ry)

            self.acc_x += dx_f
            self.acc_y += dy_f

            dx = int(self.acc_x)
            dy = int(self.acc_y)

            if dx or dy:
                self.ui.write(ecodes.EV_REL, ecodes.REL_X, dx)
                self.ui.write(ecodes.EV_REL, ecodes.REL_Y, dy)
                self.ui.syn()

                self.acc_x -= dx
                self.acc_y -= dy
    
    def read_commands(self):
        """Read and process commands from FIFO."""
        try:
            # Check if there's data to read
            r, _, _ = select.select([self.fifo_fd], [], [], 0)
            if not r:
                return
            
            # Read command
            data = os.read(self.fifo_fd, 1024).decode('utf-8').strip()
            if not data:
                return
            
            # Handle multiple commands separated by newlines
            for line in data.split('\n'):
                line = line.strip()
                if not line:
                    continue
                self._process_command(line)
                
        except (BlockingIOError, OSError):
            pass
    
    def _process_command(self, cmd):
        """Process a single command."""
        print(f"Received command: {cmd}")
        
        parts = cmd.split()
        if not parts:
            return
        
        command = parts[0].lower()
        
        if command == 'profile' and len(parts) > 1:
            profile_name = parts[1]
            self._load_profile(profile_name)
        
        elif command == 'reload':
            if self.current_profile:
                self._load_profile(self.current_profile)
            else:
                print("No profile currently loaded")
        
        elif command == 'list':
            profiles = self.list_profiles()
            print(f"Available profiles: {', '.join(profiles)}")
        
        elif command == 'stop':
            print("Stopping daemon...")
            self.running = False
        
        elif command == 'status':
            status = f"Profile: {self.current_profile or 'default'}"
            status += f", Mouse: {'on' if self.mouse_enabled else 'off'}"
            status += f", D-pad: {'on' if self.dpad_enabled else 'off'}"
            print(f"Status: {status}")
        
        elif command == 'controller' and len(parts) > 1:
            device_path = parts[1]
            self._change_device(device_path)
        
        else:
            print(f"Unknown command: {command}")
    
    def _load_profile(self, profile_name):
        """Load a profile and reinitialize controller."""
        print(f"Loading profile: {profile_name}")
        
        try:
            # Load configuration
            self.load_config(profile_name)
            
            # Setup mouse parameters
            self.setup_mouse_params()
            
            # Parse button bindings
            self.parse_bindings()
            print(f"Loaded {len(self.bindings)} button bindings")
            
            # Check D-pad enabled
            self.dpad_enabled = self.config.getboolean('dpad', 'enabled', fallback=True)
            print(f"D-pad enabled: {self.dpad_enabled}")
            
            # Check debug mode
            self.debug_enabled = self.config.getboolean('debug', 'enabled', fallback=False)
            if self.debug_enabled:
                print("Debug mode: ENABLED")
            
            # Setup device (if not already set up)
            if self.dev is None:
                self.setup_device()
                
                # Get stick calibration
                abs_rx = self.dev.absinfo(ecodes.ABS_RX)
                abs_ry = self.dev.absinfo(ecodes.ABS_RY)
                
                self.center_x = (abs_rx.max + abs_rx.min) / 2.0
                self.center_y = (abs_ry.max + abs_ry.min) / 2.0
                self.range_x = (abs_rx.max - abs_rx.min) / 2.0
                self.range_y = (abs_ry.max - abs_ry.min) / 2.0
                
                # Initialize stick position
                self.rx = self.center_x
                self.ry = self.center_y
            
            # Setup virtual input device
            self.setup_uinput()
            
            print(f"Profile '{profile_name}' loaded successfully")
            
        except Exception as e:
            print(f"Error loading profile '{profile_name}': {e}")
    
    def _change_device(self, device_path):
        """Change the input device dynamically."""
        print(f"Changing device to: {device_path}")
        
        try:
            # Close existing device if any
            if self.dev is not None:
                try:
                    self.dev.ungrab()
                except:
                    pass
                self.dev = None
            
            # Update config with new device path
            if 'device' not in self.config:
                self.config['device'] = {}
            self.config['device']['path'] = device_path
            
            # Setup new device
            self.setup_device()
            
            # Get stick calibration
            abs_rx = self.dev.absinfo(ecodes.ABS_RX)
            abs_ry = self.dev.absinfo(ecodes.ABS_RY)
            
            self.center_x = (abs_rx.max + abs_rx.min) / 2.0
            self.center_y = (abs_ry.max + abs_ry.min) / 2.0
            self.range_x = (abs_rx.max - abs_rx.min) / 2.0
            self.range_y = (abs_ry.max - abs_ry.min) / 2.0
            
            # Initialize stick position
            self.rx = self.center_x
            self.ry = self.center_y
            
            print(f"Device changed to '{device_path}' successfully")
            
        except Exception as e:
            print(f"Error changing device to '{device_path}': {e}")
    
    def run(self):
        """Main daemon loop."""
        print("Controller Daemon starting...")
        
        # Create FIFO
        self._create_fifo()
        
        # Write PID file
        self._write_pidfile()
        
        # Load default profile if exists
        profiles = self.list_profiles()
        if profiles:
            self._load_profile(profiles[0])
        else:
            print("No profiles found in profiles/ directory")
            # Load default config
            self.config = configparser.ConfigParser()
            for section, values in DEFAULT_CONFIG.items():
                self.config[section] = values.copy()
            self.setup_mouse_params()
            self.parse_bindings()
        
        print("Daemon ready! Commands: profile <name>, reload, list, status, stop")
        print(f"FIFO: echo 'profile firefox' > {FIFO_PATH}")
        
        self.running = True
        
        self._reconnect_cooldown = 0
        try:
            while self.running:
                # Read commands from FIFO
                self.read_commands()
                
                # Try to reconnect if device is gone
                if self.dev is None and self.ui is not None:
                    now = time.monotonic()
                    if now - self._reconnect_cooldown >= 3.0:
                        self._reconnect_cooldown = now
                        if self._try_reconnect():
                            self._reconnect_cooldown = 0
                
                # Process controller events if device is set up
                if self.dev is not None and self.ui is not None:
                    self.process_events()
                    self.update_mouse()
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown."""
        print("Shutting down...")
        
        if self.dev is not None:
            try:
                self.dev.ungrab()
            except:
                pass
            self.dev = None
        
        if self.ui is not None:
            self.ui.close()
            self.ui = None
        
        self._cleanup_fifo()
        self._remove_pidfile()
        
        print("Daemon stopped")


def main():
    """Entry point."""
    daemon = ControllerDaemon()
    daemon.run()


if __name__ == '__main__':
    main()
