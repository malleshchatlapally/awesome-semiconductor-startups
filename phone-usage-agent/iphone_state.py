"""Shared state for iPhone heartbeat backend (thread-safe)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class IPhoneState:
    last_heartbeat: float = 0.0
    pending_alert: Optional[Tuple[str, str]] = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record_heartbeat(self) -> None:
        with self.lock:
            self.last_heartbeat = time.time()

    def in_use(self, stale_seconds: float) -> bool:
        with self.lock:
            if self.last_heartbeat <= 0:
                return False
            return (time.time() - self.last_heartbeat) < stale_seconds

    def queue_alert(self, title: str, message: str) -> None:
        with self.lock:
            self.pending_alert = (title, message)

    def pop_pending_alert(self) -> Optional[dict]:
        with self.lock:
            if not self.pending_alert:
                return None
            title, message = self.pending_alert
            self.pending_alert = None
            return {"notify": True, "title": title, "message": message}
