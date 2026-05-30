import subprocess
import threading
import time
from .config import WINDOW_POLL_INTERVAL


class WindowTracker:
    """
    Polls the active window title at regular intervals using xdotool.

    Why polling rather than event-driven?
    X11 does support focus-change events, but subscribing to them requires
    a persistent Xlib connection and significantly more code. For educational
    purposes, polling every 0.5s is accurate enough and far simpler to follow.

    Why xdotool?
    It wraps the Xlib active-window query in a single shell command that works
    on every X11 desktop environment (GNOME, KDE, XFCE, i3, etc.) without
    any Python bindings. On Wayland the command silently returns an empty
    string — callers receive None and handle it gracefully.
    """

    def __init__(self, on_change_callback):
        """
        on_change_callback(title: str) is called whenever the active window
        title changes. It runs from the tracker's background thread — the
        callback must be thread-safe.
        """
        self._callback     = on_change_callback
        self._current      = None    # last known window title
        self._running      = False
        self._thread       = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="window-tracker",
        )
        self._thread.start()

    def stop(self):
        self._running = False

    def _get_active_window_title(self) -> str | None:
        """
        Shell out to xdotool to get the focused window title.
        Returns None on any error (Wayland, no display, xdotool not installed).
        """
        try:
            # getactivewindow gets the XID; getwindowname converts it to a title.
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True,
                text=True,
                timeout=1.0,    # don't block forever if xdotool hangs
            )
            title = result.stdout.strip()
            return title if title else None
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # FileNotFoundError: xdotool not installed
            # TimeoutExpired: display server is unresponsive
            return None

    def _poll_loop(self):
        """Check the active window title every WINDOW_POLL_INTERVAL seconds."""
        while self._running:
            title = self._get_active_window_title()
            # Only fire the callback when the title actually changes —
            # avoids spamming the log with identical window entries every 0.5s.
            if title and title != self._current:
                self._current = title
                try:
                    self._callback(title)
                except Exception:
                    pass    # callbacks must not crash the tracker thread
            time.sleep(WINDOW_POLL_INTERVAL)
