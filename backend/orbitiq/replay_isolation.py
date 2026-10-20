"""Scoped Python audit policy for operator replay, inert for ordinary API work.

This is defense in depth for the fixed trusted replay implementation, not an OS
sandbox for executing hostile Python or native extensions. Bundle members are data.
"""

import sys
from contextlib import contextmanager
from contextvars import ContextVar

_ACTIVE = ContextVar("orbitiq_offline_replay", default=None)
_EVENTS = {
    "socket.connect": "network",
    "socket.getaddrinfo": "network",
    "socket.gethostbyname": "network",
    "socket.gethostbyaddr": "network",
    "socket.sendto": "network",
    "socket.sendmsg": "network",
    "sqlite3.connect": "database",
    "subprocess.Popen": "process",
    "os.system": "process",
    "os.exec": "process",
    "os.posix_spawn": "process",
    "os.fork": "process",
    "os.forkpty": "process",
    "pty.spawn": "process",
}


class ReplayIsolationError(RuntimeError):
    def __init__(self, category):
        self.category = category
        super().__init__("Offline replay forbids " + category + " access")


def _audit(event, _args):
    counts = _ACTIVE.get()
    if counts is not None and event in _EVENTS:
        category = _EVENTS[event]
        counts[category] += 1
        raise ReplayIsolationError(category)


sys.addaudithook(_audit)  # Permanent hook; policy activates only inside this context.


@contextmanager
def offline_replay():
    counts = {"network": 0, "database": 0, "process": 0}
    token = _ACTIVE.set(counts)
    try:
        yield counts
    finally:
        _ACTIVE.reset(token)
