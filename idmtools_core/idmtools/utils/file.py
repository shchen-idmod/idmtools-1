import os
from os import DirEntry
from pathlib import Path
from typing import Iterable


def scan_directory(basedir: str, recursive: bool = True) -> Iterable[DirEntry]:
    """
    Scan a directory recursively or not.

    Args:
        basedir: The root directory to start from.
        recursive: True to search the subfolders recursively; False to stay in the root directory.

    Returns:
        An iterator yielding all the files found.
    """
    for entry in os.scandir(basedir):
        if entry.is_file():
            yield entry
        elif recursive:
            yield from scan_directory(entry.path)


def get_idmtools_root() -> Path:
    """
    Return the root directory of the idmtools core package
    Returns: a Path object for the root directory
    """
    return Path(__file__).parent.parent
