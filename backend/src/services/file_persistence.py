"""Local editor file locking and atomic text replacement; no feature validation."""
from contextlib import contextmanager
import os
import tempfile


@contextmanager
def exclusive_edit(target, conflict_type, message):
    """Hold a sibling lock; never remove a lock owned by another editor."""
    lock = target.with_suffix('.lock')
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise conflict_type(message) from None
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()


def replace_text(target, content, *, prefix, before_replace=None):
    """Flush a sibling temporary file, optionally recheck revision, then replace.

    Callers hold their edit lock and handle serialization and revision policy.
    Failures before replacement leave the original file intact and clean up the
    temporary file. This does not coordinate writers that ignore the lock.
    """
    fd, temporary = tempfile.mkstemp(dir=target.parent, prefix=prefix, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if before_replace is not None:
            before_replace()
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
