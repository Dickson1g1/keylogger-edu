import logging
import threading
from logging.handlers import RotatingFileHandler
from datetime import datetime
from .config import LOG_DIR, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT, FLUSH_INTERVAL


class LogWriter:
    """
    Thread-safe buffered log writer with automatic size-based rotation.

    Design decisions:
    - We use Python's RotatingFileHandler rather than rolling our own rotation
      logic. It handles rename-and-reopen atomically and integrates cleanly
      with the logging module's formatter infrastructure.
    - A threading.Lock protects both the in-memory buffer and all handler
      calls. The listener runs in a background thread; the flush timer also
      runs in its own thread — both write through this lock.
    - We buffer for FLUSH_INTERVAL seconds rather than writing every keystroke.
      Disk I/O on every key press would be audible on HDD systems and wasteful
      on SSD systems with write amplification concerns.
    """

    def __init__(self):
        # Create the log directory if it doesn't exist yet
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # _lock serialises all access to _buffer and _handler from any thread
        self._lock    = threading.Lock()
        self._buffer  = []          # list of strings waiting to be flushed
        self._running = False       # flush timer loop control flag

        # Configure a rotating file handler via the standard logging module.
        # maxBytes: rotate when file reaches this size.
        # backupCount: keep this many old files (keylog.txt.1, .2, .3).
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))

        self._logger = logging.getLogger("keylogger")
        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(handler)
        # Prevent log records from bubbling up to the root logger's console handler
        self._logger.propagate = False

    def start(self):
        """Start the background flush timer thread."""
        self._running = True
        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            daemon=True,     # daemon thread: dies automatically when main thread exits
            name="flush-timer",
        )
        self._flush_thread.start()

    def stop(self):
        """Flush remaining buffer and stop the timer thread."""
        self._running = False
        self._flush_now()   # final flush before exit

    def write(self, text: str):
        """
        Append text to the in-memory buffer.
        Called from the keyboard listener thread — must be fast and non-blocking.
        """
        with self._lock:
            self._buffer.append(text)

    def _flush_loop(self):
        """Timer loop: wake every FLUSH_INTERVAL seconds and flush the buffer."""
        import time
        while self._running:
            time.sleep(FLUSH_INTERVAL)
            self._flush_now()

    def _flush_now(self):
        """
        Move the entire buffer to disk in one logger call.
        Joining with empty string preserves the exact character sequence —
        no extra spaces or newlines are inserted between keystrokes.
        """
        with self._lock:
            if not self._buffer:
                return
            chunk = "".join(self._buffer)
            self._buffer.clear()

        # Write outside the lock to minimise contention —
        # the buffer is already cleared, so new writes can proceed.
        self._logger.info(chunk)
