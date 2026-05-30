```
 ██╗  ██╗███████╗██╗   ██╗██╗      ██████╗  ██████╗  ██████╗ ███████╗██████╗ 
 ██║ ██╔╝██╔════╝╚██╗ ██╔╝██║     ██╔═══██╗██╔════╝ ██╔════╝ ██╔════╝██╔══██╗
 █████╔╝ █████╗   ╚████╔╝ ██║     ██║   ██║██║  ███╗██║  ███╗█████╗  ██████╔╝
 ██╔═██╗ ██╔══╝    ╚██╔╝  ██║     ██║   ██║██║   ██║██║   ██║██╔══╝  ██╔══██╗
 ██║  ██╗███████╗   ██║   ███████╗╚██████╔╝╚██████╔╝╚██████╔╝███████╗██║  ██║
 ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝

 ███████╗██████╗ ██╗   ██╗
 ██╔════╝██╔══██╗██║   ██║
 █████╗  ██║  ██║██║   ██║
 ██╔══╝  ██║  ██║██║   ██║
 ███████╗██████╔╝╚██████╔╝
 ╚══════╝╚═════╝  ╚═════╝ 

   event handling · file i/o · ethical considerations · python
```

# keylogger-edu

> An educational keyboard event capture tool built in Python.
> Demonstrates OS-level input handling, threaded file I/O, log rotation,
> active window tracking, and runtime toggle control — for learning purposes only.

---

> **⚠ ETHICAL USE NOTICE**
> This project is strictly for **educational use on machines you own**.
> Running a keylogger on any system without explicit written consent from
> the owner is illegal under computer fraud and abuse laws in virtually
> every jurisdiction. The author assumes no liability for misuse.

---

## What it does

`keylogger-edu` hooks into the OS keyboard event stream using `pynput` and
logs every keystroke with context — which window was active, what time it
happened, and what key was pressed. It demonstrates real-world patterns
used in security research: event-driven I/O, thread-safe buffering, log
rotation, and simulated remote delivery.

```
--- Session started 2024-11-03 14:22:01 ---

[14:22:03] [Terminal — bash]
ls -la[ENTER]
cd Documents[ENTER]

[14:22:18] [Firefox — GitHub]
hello world[ENTER]

[14:22:30] [CAPTURE PAUSED]
[14:22:35] [CAPTURE RESUMED]

--- Session ended 2024-11-03 14:22:40 ---
```

---

## Features

- **Real-time keyboard event capture** with microsecond-precision timestamps
  via `pynput` — no root required on Linux (uses X11/Wayland display API)
- **Active window tracking** — logs the focused application title whenever
  focus changes, giving context to every block of keystrokes
- **Log rotation** — automatically rotates `keylog.txt` at 5 MB and keeps
  up to 3 backup files using Python's `RotatingFileHandler`
- **F9 toggle** — pause and resume capture at runtime without stopping the
  process; toggle events are always recorded regardless of pause state
- **Buffered writes** — keystrokes are held in memory and flushed to disk
  every 2 seconds, reducing I/O overhead compared to per-keystroke writes
- **Simulated webhook delivery** — demonstrates C2 exfiltration patterns
  by batching keystrokes and POST-ing to a configurable localhost endpoint
  (disabled by default; localhost only)
- **Thread-safe design** — listener thread, flush timer thread, and window
  tracker thread all share state through `threading.Lock`
- **Graceful shutdown** — Ctrl-C and SIGTERM flush all buffered data to disk
  before exit; no keystrokes are lost on clean shutdown
- **Special key labels** — non-printable keys rendered as `[ENTER]`,
  `[BACKSPACE]`, `[TAB]`, `[CTRL]`, `[ALT]`, etc. for readable logs

---

## Requirements

- Linux (tested on Kali, Ubuntu 22.04+, Debian 12)
- Python 3.10+
- X11 display session (not headless SSH — pynput needs a display)
- `xdotool` for active window tracking

```bash
# Ubuntu / Debian / Kali
sudo apt install xdotool

pip install pynput requests
```

---

## Installation

```bash
git clone https://github.com/Dickson1g1/keylogger-edu.git
cd keylogger-edu

# Option A — virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install pynput requests

# Option B — system-wide on Kali / Debian
pip install pynput requests --break-system-packages
```

---

## Usage

```bash
# Start capture (F9 to toggle, Ctrl-C to stop)
python run.py

# View the live log
tail -f logs/keylog.txt

# Check rotated log files
ls -lh logs/
```

---

## Project structure

```
keylogger-edu/
├── keylogger/
│   ├── __init__.py
│   ├── config.py        # all tuneable constants (paths, sizes, toggle key)
│   ├── writer.py        # thread-safe buffered log writer + rotation
│   ├── window.py        # active window title tracker via xdotool
│   ├── webhook.py       # simulated localhost C2 delivery
│   └── capture.py       # pynput keyboard listener + F9 toggle logic
├── logs/                # created automatically on first run
│   └── keylog.txt
└── run.py               # entry point
```

---

## Configuration

All settings are in `keylogger/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `LOG_MAX_BYTES` | 5 MB | Rotate log file at this size |
| `LOG_BACKUP_COUNT` | 3 | Number of rotated backups to keep |
| `TOGGLE_KEY` | `f9` | Key to pause/resume capture |
| `FLUSH_INTERVAL` | 2.0 s | How often to flush buffer to disk |
| `WINDOW_POLL_INTERVAL` | 0.5 s | How often to check the active window |
| `WEBHOOK_ENABLED` | `False` | Enable localhost webhook delivery |
| `WEBHOOK_BATCH` | 50 chars | Deliver after this many keystrokes |

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Clean shutdown (Ctrl-C or SIGTERM) |
| `1` | Fatal startup error |

---

## Concepts covered

- `pynput` keyboard listener API and key object types
- `threading.Thread`, `threading.Lock`, and daemon threads
- `logging.handlers.RotatingFileHandler` for size-based log rotation
- Producer-consumer buffer pattern with timed flush
- `subprocess.run` for shell integration (xdotool window queries)
- `signal.signal` for clean Ctrl-C / SIGTERM handling
- Simulated HTTP exfiltration with `requests.post`

---

## Legal notice

This tool is provided for **educational and authorized security research
purposes only**. You are solely responsible for ensuring you have explicit
permission before running this software on any system. Unauthorized
interception of keyboard input is a criminal offense in most countries.

---

## License

MIT — for educational use only. See above legal notice.
