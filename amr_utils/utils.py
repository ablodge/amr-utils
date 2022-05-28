import os
import sys
from contextlib import contextmanager
from typing import Any


def class_name(object: Any):
    """
    Get the class name of object as a string
    Args:
        object: an object

    Returns:
        str: class name
    """
    if isinstance(object, type):
        return object.__name__
    return object.__class__.__name__


@contextmanager
def silence_warnings():
    """
    Context for silencing warnings and messages to stderr from a function or code block
    Usage Example:
    ```
    with silence_warnings():
        noisy_function()
    ```
    """
    stderr = sys.stderr
    devnull = open(os.devnull, 'w')
    try:
        sys.stderr = devnull
        yield
    finally:
        sys.stderr = stderr
        devnull.close()