from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote


def from_local_uri(uri: str) -> Path:
    """
    Turn a local file uri to an absolute path.

    Compatibility patch for https://docs.python.org/3/library/pathlib.html#pathlib.Path.from_uri.
    """

    return Path(unquote(uri).removeprefix("file://"))
