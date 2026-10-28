"""Login rate limiting (issue #8). Kept in this process's memory: see the README for what that means.

Two limits, both checked before the password:
  - Per email: after max_failures failed logins within window_seconds, every attempt for that email is
    refused until the oldest of those failures is window_seconds old, even with the right password.
    It applies to any email, registered or not, so the limit itself doesn't reveal who has an account.
  - Per client IP: at most max_per_ip logins checked per minute, successful or not. This stops one
    machine trying one password against many emails, which the per-email limit can't see.
Refused attempts are not counted, so waiting the Retry-After time always works.
"""
import math
import time
from collections import defaultdict, deque

from .config import LOGIN_MAX_FAILURES, LOGIN_MAX_PER_IP, LOGIN_WINDOW_SECONDS

IP_WINDOW_SECONDS = 60


class LoginLimiter:
    def __init__(self, max_failures, window_seconds, max_per_ip, clock=time.monotonic):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.max_per_ip = max_per_ip
        self.clock = clock  # tests pass a fake clock so they don't have to sleep
        self.reset()

    def reset(self):
        self.failures = defaultdict(deque)  # email -> times of recent failed logins, oldest first
        self.attempts = defaultdict(deque)  # IP -> times of recent logins checked, oldest first

    def _recent(self, times, window):
        """Drop the times older than the window and return what is left."""
        while times and times[0] <= self.clock() - window:
            times.popleft()
        return times

    def _wait_for(self, times, window, limit):
        """Seconds until there is room under the limit again; 0 if there is room now."""
        recent = self._recent(times, window)
        if len(recent) < limit:
            return 0
        return math.ceil(recent[0] + window - self.clock())

    def seconds_to_wait(self, email, ip):
        """0 if this login may be checked now, otherwise how many seconds to wait."""
        return max(
            self._wait_for(self.failures[email], self.window_seconds, self.max_failures),
            self._wait_for(self.attempts[ip], IP_WINDOW_SECONDS, self.max_per_ip),
        )

    def record_attempt(self, ip):
        self.attempts[ip].append(self.clock())

    def record_failure(self, email):
        self.failures[email].append(self.clock())

    def record_success(self, email):
        self.failures.pop(email, None)


def too_many_attempts_message(seconds):
    minutes = math.ceil(seconds / 60)
    return f"Too many attempts. Try again in {minutes} minute{'' if minutes == 1 else 's'}."


login_limiter = LoginLimiter(LOGIN_MAX_FAILURES, LOGIN_WINDOW_SECONDS, LOGIN_MAX_PER_IP)
