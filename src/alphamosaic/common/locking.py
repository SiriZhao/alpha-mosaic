"""Process-scoped local research leases; file contents never establish liveness."""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from alphamosaic.common.paths import unredirected


class ResearchBusyError(ValueError):
    pass


@contextmanager
def exclusive_lease(path: Path) -> Iterator[None]:
    """Acquire a nonblocking OS lock, released automatically on process exit."""
    path = unredirected(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    unredirected(path)
    with path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ResearchBusyError("another local research execution holds the OS lease") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
