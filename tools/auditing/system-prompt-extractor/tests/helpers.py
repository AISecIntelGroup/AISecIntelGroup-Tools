"""Shared test utilities for system-prompt-extractor."""

from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO


@contextmanager
def capture_output():
    """Capture stdout and stderr; yields (stdout, stderr) StringIO buffers."""
    out = StringIO()
    err = StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        yield out, err
