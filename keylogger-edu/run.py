#!/usr/bin/env python3
"""
run.py — Educational keylogger entry point.

ETHICAL USE ONLY. Run only on machines you own or have explicit written
permission to monitor. Unauthorized use is illegal.
"""

import sys
import signal
from keylogger.capture import KeyCapture
from keylogger.config  import LOG_FILE, TOGGLE_KEY

BANNER = f"""
╔══════════════════════════════════════════════════╗
║       EDUCATIONAL KEYLOGGER — LOCAL USE ONLY     ║
╠══════════════════════════════════════════════════╣
║  Log file : {str(LOG_FILE):<38}║
║  Toggle   : {TOGGLE_KEY.upper():<38}║
║  Stop     : Ctrl-C                               ║
╚══════════════════════════════════════════════════╝
"""

def main() -> int:
    print(BANNER)

    capture = KeyCapture()

    # Handle Ctrl-C and SIGTERM gracefully — flush buffers before exit
    def _shutdown(sig, frame):
        print("\nShutting down — flushing buffers...")
        capture.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        capture.start()   # blocks until stopped
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
