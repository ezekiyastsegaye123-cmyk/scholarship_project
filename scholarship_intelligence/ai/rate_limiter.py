"""In-memory rate limiter for AI counselor endpoints."""
import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


class AIRateLimiter:
    """Sliding-window rate limiter per user/account."""

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, account_id: str) -> Tuple[bool, int, int]:
        """Checks whether the request is permitted.

        Returns:
            (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            # Prune old timestamps
            self._requests[account_id] = [
                ts for ts in self._requests[account_id] if ts > window_start
            ]
            current_count = len(self._requests[account_id])

            if current_count < self.max_requests:
                self._requests[account_id].append(now)
                remaining = self.max_requests - (current_count + 1)
                return True, remaining, 0
            else:
                oldest = self._requests[account_id][0]
                retry_after = max(1, int(oldest + self.window_seconds - now))
                return False, 0, retry_after

    def reset(self, account_id: Optional[str] = None):
        """Resets the rate limiter for testing."""
        with self._lock:
            if account_id:
                self._requests.pop(account_id, None)
            else:
                self._requests.clear()


# Global singleton instance
ai_rate_limiter = AIRateLimiter()
