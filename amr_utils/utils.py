import os
import sys
from contextlib import contextmanager
from typing import Any


def class_name(object: Any):
    if isinstance(object, type):
        return object.__name__
    return object.__class__.__name__


@contextmanager
def silence_warnings():
    stderr = sys.stderr
    devnull = open(os.devnull, 'w')
    try:
        sys.stderr = devnull
        yield
    finally:
        sys.stderr = stderr
        devnull.close()