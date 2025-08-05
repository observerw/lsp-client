"""Re-export some lsp types for convenience."""

from __future__ import annotations

import os
from typing import Protocol

from attrs import AttrsInstance
from lsprotocol import types

Position = types.Position
Range = types.Range

AnyPath = str | os.PathLike[str]

type Request = AttrsInstance
type Notification = AttrsInstance


class Response[T](Protocol):
    """
    Duck-type schema for extracting the result type from `lsprotocol` Response schema.

    e.g.

    ```python
    def result[T](self, resp: Response[T]) -> T:
        return resp.result
    ```
    """

    result: T
